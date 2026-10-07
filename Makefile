export UID := $(shell id -u)
export GID := $(shell id -g)

NAME  := amiga-1000-keyboard
BOARD := pcb/$(NAME).kicad_pcb
SCH   := pcb/$(NAME).kicad_sch
BUILD := build
KICAD := docker compose run --rm kicad kicad-cli
TOOLS := docker compose run --rm tools

.PHONY: drc bom fab print plate render release clean

# Refill the pours, then fail on any DRC error or schematic/board mismatch (silkscreen warnings don't fail).
drc:
	mkdir -p $(BUILD)
	$(KICAD) pcb drc --refill-zones --schematic-parity --severity-error --exit-code-violations \
		-o $(BUILD)/drc.rpt $(BOARD)

bom:
	$(KICAD) sch export bom --group-by "Part,Footprint,DNP" \
		--fields 'Reference,QUANTITY,Part,Footprint,DNP' --labels 'Refs,Qty,Part,Footprint,DNP' \
		--sort-field Reference -o pcb/bom.csv $(SCH)

# Gerbers and Excellon drill files, zipped for the board house.
fab:
	rm -rf $(BUILD)/fab && mkdir -p $(BUILD)/fab/gerbers
	$(KICAD) pcb export gerbers --check-zones --subtract-soldermask --no-x2 \
		--layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts -o $(BUILD)/fab/gerbers $(BOARD)
	$(KICAD) pcb export drill --format excellon --excellon-separate-th --excellon-units mm \
		--generate-map --map-format pdf -o $(BUILD)/fab/gerbers/ $(BOARD)
	$(TOOLS) sh -c 'cd $(BUILD)/fab/gerbers && python -m zipfile -c ../$(NAME)-gerbers.zip *'

# 1:1 print sheets for checking fit against the case and plate.
print:
	mkdir -p $(BUILD)/print
	$(KICAD) pcb export svg --mode-single \
		--layers Edge.Cuts,F.Mask,F.SilkS,Dwgs.User --page-size-mode 2 --exclude-drawing-sheet \
		--black-and-white --drill-shape-opt 2 -o $(BUILD)/print/board.svg $(BOARD)
	$(TOOLS) python tools/print_sheets.py $(BUILD)/print/board.svg $(BUILD)/print

# Switch plate generated from the PCB: a plate-only KiCad board plus a DXF for laser cutting.
plate:
	mkdir -p $(BUILD)/plate
	$(TOOLS) python tools/make_plate.py $(BOARD) $(BUILD)/plate/$(NAME)-plate.kicad_pcb
	$(KICAD) pcb export dxf --mode-single --layers Edge.Cuts --output-units mm --use-contours \
		-o $(BUILD)/plate/$(NAME)-plate.dxf $(BUILD)/plate/$(NAME)-plate.kicad_pcb
	rm -rf $(BUILD)/plate/gerbers && mkdir -p $(BUILD)/plate/gerbers
	$(KICAD) pcb export gerbers --no-x2 --layers Edge.Cuts,F.Mask,B.Mask \
		-o $(BUILD)/plate/gerbers $(BUILD)/plate/$(NAME)-plate.kicad_pcb
	$(TOOLS) sh -c 'cd $(BUILD)/plate/gerbers && python -m zipfile -c ../$(NAME)-plate-gerbers.zip *'

# 3D renders for the README (published to the renders branch by CI).
RENDER := pcb render --quality high --background transparent
render: plate
	mkdir -p $(BUILD)/render
	$(KICAD) $(RENDER) --side top --width 2400 --height 940 --zoom 2.3 -o $(BUILD)/render/board-top.png $(BOARD)
	$(KICAD) $(RENDER) --width 2400 --height 1200 --perspective --rotate "-45,0,-20" --zoom 1.35 \
		-o $(BUILD)/render/board-iso.png $(BOARD)
	$(KICAD) $(RENDER) --side top --width 2400 --height 940 --zoom 2.3 \
		-o $(BUILD)/render/plate-top.png $(BUILD)/plate/$(NAME)-plate.kicad_pcb

# Everything a release ships, collected in build/release.
release: drc bom fab print plate
	rm -rf $(BUILD)/release && mkdir -p $(BUILD)/release
	cp $(BUILD)/fab/$(NAME)-gerbers.zip pcb/bom.csv $(BUILD)/print/*.pdf $(BUILD)/release/
	cp $(BUILD)/fab/gerbers/*-drl_map.pdf $(BUILD)/release/ 2>/dev/null || true
	cp $(BUILD)/plate/$(NAME)-plate.dxf $(BUILD)/plate/$(NAME)-plate-gerbers.zip $(BUILD)/release/

clean:
	rm -rf $(BUILD)

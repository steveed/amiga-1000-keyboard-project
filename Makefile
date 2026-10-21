export UID := $(shell id -u)
export GID := $(shell id -g)

NAME  := amiga-1000-keyboard
BOARD := pcb/$(NAME).kicad_pcb
SCH   := pcb/$(NAME).kicad_sch
BUILD := build
# Printed on the back silkscreen: the release tag, or git describe for local builds.
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)
KICAD := docker compose run --rm kicad kicad-cli
VARS  := -D VERSION=$(VERSION)
TOOLS := docker compose run --rm tools
OPENSCAD := docker compose run --rm -T openscad --backend=manifold
FIRMWARE := docker compose run --rm -T firmware
CASE_PARTS := top_left top_right bottom_left bottom_right
# Which jack the case takes (case/a1000_case.scad, jack_type): nose, or 616e.  616e files get a -616e suffix.
JACK ?= nose
JACK_VARS := -D "jack_type=\"$(JACK)\""
JACK_SUF  := $(if $(filter nose,$(JACK)),,-$(JACK))

.PHONY: drc bom fab print plate case case-one case-jack case-joint label rev2-sch rev2-pcb rev2-route rev2-drc rev2-fab rev2-plate rev2-jlc firmware firmware-test firmware-flash render release rev2-release clean

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
	$(KICAD) pcb export gerbers $(VARS) --check-zones --subtract-soldermask --no-x2 \
		--layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts -o $(BUILD)/fab/gerbers $(BOARD)
	$(KICAD) pcb export drill --format excellon --excellon-separate-th --excellon-units mm \
		--generate-map --map-format pdf -o $(BUILD)/fab/gerbers/ $(BOARD)
	$(TOOLS) sh -c 'cd $(BUILD)/fab/gerbers && python -m zipfile -c ../$(NAME)-gerbers.zip *'

# 1:1 print sheets for checking fit against the case and plate.
print:
	mkdir -p $(BUILD)/print
	$(KICAD) pcb export svg $(VARS) --mode-single \
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

# Printable case parts (STL) and an assembly preview, from case/a1000_case.scad.
case:
	mkdir -p $(BUILD)/case
	for p in $(CASE_PARTS); do \
		$(OPENSCAD) --export-format=binstl -D "part=\"$$p\"" $(JACK_VARS) -o $(BUILD)/case/$(NAME)-case-$$p$(JACK_SUF).stl case/a1000_case.scad || exit 1; \
	done
	$(OPENSCAD) --render --imgsize=2400,1000 --camera=195,60,0,55,0,20,620 --projection=p $(JACK_VARS) \
		-o $(BUILD)/case/case-assembly$(JACK_SUF).png case/a1000_case.scad

# Stickers for the label recess under the case, one per board revision, 1:1.
label:
	mkdir -p $(BUILD)/case
	for r in 1 2; do \
		$(TOOLS) python tools/make_label.py $(BUILD)/case/$(NAME)-label-rev$$r.svg $$r || exit 1; \
	done

# The case in two parts, each shell in one piece, for a bed that takes 406 x 158 mm.
case-one:
	mkdir -p $(BUILD)/case
	for p in top bottom; do \
		$(OPENSCAD) --export-format=binstl -D "part=\"$$p\"" -D split=false $(JACK_VARS) -o $(BUILD)/case/$(NAME)-case-$$p$(JACK_SUF).stl case/a1000_case.scad || exit 1; \
	done

# Test prints of just the jack corner of each shell, to try the jack before printing the whole case.
case-jack:
	mkdir -p $(BUILD)/case
	for p in jack_test_bottom jack_test_top; do \
		$(OPENSCAD) --export-format=binstl -D "part=\"$$p\"" $(JACK_VARS) -o $(BUILD)/case/$(NAME)-case-$$p$(JACK_SUF).stl case/a1000_case.scad || exit 1; \
	done

# Test prints of a strip along the front of each shell, across both glue joints and a snap.
case-joint:
	mkdir -p $(BUILD)/case
	for p in joint_test_top_left joint_test_top_right joint_test_bottom_left joint_test_bottom_right; do \
		$(OPENSCAD) --export-format=binstl -D "part=\"$$p\"" -o $(BUILD)/case/$(NAME)-case-$$p.stl case/a1000_case.scad || exit 1; \
	done

# Rev 2 (ATmega32U4, surface mount): regenerate the schematic from tools/gen_rev2_sch.py, then
# fail on any ERC error.  The library-table warnings from the bare container are not errors.
REV2 := pcb/rev_2/$(NAME)-rev2
rev2-sch:
	mkdir -p $(BUILD)
	docker compose run --rm -T --entrypoint python3 kicad tools/gen_rev2_sch.py
	$(KICAD) sch erc --severity-error --exit-code-violations -o $(BUILD)/rev2-erc.rpt $(REV2).kicad_sch

# Rev 2 board: rebuild it from rev 1's outline and the rev 2 schematic.  This places parts only;
# `make rev2-route` then routes it.
rev2-pcb: rev2-sch
	docker compose run --rm -T --entrypoint python3 kicad tools/gen_rev2_pcb.py

# Rev 2 routing with KiCadRoutingTools, in its krt:local image (see pcb/rev_2/README.md); the passes
# are in tools/rev2_route.json.  Then remove the vias and tracks left dangling (tools/rev2_cleanup.py).
rev2-route:
	docker run --rm -u $(UID):$(GID) -v "$(CURDIR)":/repo krt:local python3 /repo/tools/route_rev2.py
	@for i in 1 2 3 4 5 6; do \
		$(KICAD) pcb drc --refill-zones --severity-warning --format json -o $(BUILD)/rev2-dangling.json \
			$(REV2).kicad_pcb >/dev/null 2>&1; \
		n=$$(docker compose run --rm -T tools python tools/rev2_cleanup.py $(BUILD)/rev2-dangling.json 2>/dev/null | tail -1); \
		echo "cleanup: removed $$n dangling vias and tracks"; [ "$$n" = 0 ] && break; \
	done

# Rev 2 gerbers and drill files for JLCPCB, zipped.
rev2-fab:
	rm -rf $(BUILD)/rev2-fab && mkdir -p $(BUILD)/rev2-fab/gerbers
	$(KICAD) pcb export gerbers $(VARS) --check-zones --subtract-soldermask --no-x2 \
		--layers F.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts \
		-o $(BUILD)/rev2-fab/gerbers $(REV2).kicad_pcb
	$(KICAD) pcb export drill --format excellon --excellon-separate-th --excellon-units mm \
		--generate-map --map-format pdf -o $(BUILD)/rev2-fab/gerbers/ $(REV2).kicad_pcb
	$(TOOLS) sh -c 'cd $(BUILD)/rev2-fab/gerbers && python -m zipfile -c ../$(NAME)-rev2-gerbers.zip *'

# Rev 2 MX plates, US and ISO (one board, two plates): KiCad board, DXF, SVG and a gerber zip each.
rev2-plate:
	mkdir -p $(BUILD)/rev2-plate
	for v in us iso; do \
		P=$(BUILD)/rev2-plate/$(NAME)-rev2-plate-$$v; \
		$(TOOLS) python tools/make_plate.py $(REV2).kicad_pcb $$P.kicad_pcb $$v || exit 1; \
		$(KICAD) pcb export dxf --mode-single --layers Edge.Cuts --output-units mm --use-contours -o $$P.dxf $$P.kicad_pcb; \
		rm -rf $$P-gerbers && mkdir -p $$P-gerbers; \
		$(KICAD) pcb export gerbers --no-x2 --layers Edge.Cuts,F.Mask,B.Mask -o $$P-gerbers $$P.kicad_pcb; \
		$(TOOLS) sh -c "cd $$P-gerbers && python -m zipfile -c ../$$(basename $$P)-gerbers.zip *"; \
	done

# Rev 2 assembly files for JLCPCB: BOM (by LCSC part number) and placement.
rev2-jlc:
	mkdir -p $(BUILD)/rev2-jlc
	$(KICAD) sch export bom --fields 'Reference,Value,Footprint,LCSC,$${DNP}' --labels 'Reference,Value,Footprint,LCSC,DNP' \
		--group-by 'Value,Footprint,LCSC,$${DNP}' --ref-range-delimiter '' -o $(BUILD)/rev2-jlc/bom-kicad.csv $(REV2).kicad_sch
	$(KICAD) pcb export pos --format csv --units mm --side both -o $(BUILD)/rev2-jlc/pos-kicad.csv $(REV2).kicad_pcb
	$(TOOLS) python tools/jlc_export.py $(BUILD)/rev2-jlc/bom-kicad.csv $(BUILD)/rev2-jlc/pos-kicad.csv $(BUILD)/rev2-jlc

# Rev 2 DRC with schematic parity.
rev2-drc:
	mkdir -p $(BUILD)
	$(KICAD) pcb drc --refill-zones --schematic-parity --severity-error --exit-code-violations \
		-o $(BUILD)/rev2-drc.rpt $(REV2).kicad_pcb

# Rev 2 firmware (firmware/): regenerate the keymap from the rev 2 matrix, then build the hex in
# build/firmware/.  firmware-test runs the host-side unit tests.
firmware:
	$(TOOLS) python tools/gen_keymap.py
	$(FIRMWARE) make -C firmware

firmware-test:
	$(FIRMWARE) make -C firmware test

# Flash over USB with the 32U4's DFU bootloader.  This one runs on the host (brew install
# dfu-programmer): Docker Desktop on macOS can't pass USB devices through to a container.
firmware-flash: firmware
	dfu-programmer atmega32u4 erase --force
	dfu-programmer atmega32u4 flash $(BUILD)/firmware/$(NAME)-rev2.hex
	dfu-programmer atmega32u4 launch

# 3D renders for the README (published to the renders branch by CI).
RENDER := pcb render $(VARS) --quality high --background transparent
render: plate
	mkdir -p $(BUILD)/render
	$(KICAD) $(RENDER) --side top --width 2400 --height 940 --zoom 2.3 -o $(BUILD)/render/board-top.png $(BOARD)
	$(KICAD) $(RENDER) --width 2400 --height 1200 --perspective --rotate "-45,0,-20" --zoom 1.35 \
		-o $(BUILD)/render/board-iso.png $(BOARD)
	$(TOOLS) python -c "import cairosvg; cairosvg.svg2png(url='$(BUILD)/plate/$(NAME)-plate.svg', \
		write_to='$(BUILD)/render/plate-top.png', output_width=2400)"

# Everything a release ships, collected in build/release.
release: drc bom fab print plate
	rm -rf $(BUILD)/release && mkdir -p $(BUILD)/release
	cp $(BUILD)/fab/$(NAME)-gerbers.zip pcb/bom.csv $(BUILD)/print/*.pdf $(BUILD)/release/
	cp $(BUILD)/fab/gerbers/*-drl_map.pdf $(BUILD)/release/ 2>/dev/null || true
	cp $(BUILD)/plate/$(NAME)-plate.dxf $(BUILD)/plate/$(NAME)-plate-gerbers.zip $(BUILD)/release/

# Everything a rev 2 release ships, collected in build/rev2-release: the JLCPCB order files, both
# MX plates and the firmware hex.
rev2-release: rev2-drc rev2-fab rev2-jlc rev2-plate firmware-test firmware
	rm -rf $(BUILD)/rev2-release && mkdir -p $(BUILD)/rev2-release
	cp $(BUILD)/rev2-fab/$(NAME)-rev2-gerbers.zip $(BUILD)/rev2-jlc/bom-jlc.csv $(BUILD)/rev2-jlc/cpl-jlc.csv \
		$(BUILD)/rev2-release/
	cp $(BUILD)/rev2-plate/*-plate-us-gerbers.zip $(BUILD)/rev2-plate/*-plate-iso-gerbers.zip \
		$(BUILD)/rev2-plate/*-plate-us.dxf $(BUILD)/rev2-plate/*-plate-iso.dxf $(BUILD)/rev2-release/
	cp $(BUILD)/firmware/$(NAME)-rev2.hex $(BUILD)/rev2-release/

clean:
	rm -rf $(BUILD)

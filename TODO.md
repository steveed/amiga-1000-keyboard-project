# TODO

1. ~~**PCB measurements**~~ - done from photos, scans and calipers (`docs/measurements.md`).
   Overall length checked by caliper from the case holes (389.4 mm vs 389.25 drawn).
2. ~~**Layout/routing**~~ - placed to match the reproduction board and routed with KiCadRoutingTools.
3. **Print test fit** - `make print`, print at 100%, and test against the case, plate and keycaps.
4. ~~**Create plate from original**~~ - version 1 is a 1.2 mm FR4 plate generated from the PCB (`make plate`).
   A steel version needs the folded edges measured.
5. **Fab** - tag a release (`v*`) to build gerbers, then order boards.
6. **Custom case** - first pass shaped from a 1:8 model (`make case`, `case/README.md`).
   Still to measure: plate to PCB spacing, plate height under the keycaps, and whether Y1 lies flat.

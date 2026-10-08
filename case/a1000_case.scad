// a1000_case.scad
//
// Printable case for the Amiga 1000 keyboard PCB and switch plate, shaped after the original.
//
// The outside (outline, edge profile, parting groove, key openings, label and badge recesses,
// feet) is measured from a 1:8 scale model of the original keyboard, fitted to this board's
// switch positions (66 keycaps matched to 0.27 mm RMS at a scale of 7.99).  The inside (how the
// plate and PCB are held, screws, the joints for printing) is designed here.  See README.md
// for the numbers and what is still assumed.
//
// Coordinates are the PCB's, as in docs/measurements.md: x from the PCB's left edge, y up from
// its front edge (+y is away from the typist), component side up.  z = 0 is the parting line
// between the top and bottom shells, in the middle of the groove that runs round the case.
//
// Four printed parts, each fits a 256 x 256 mm bed:
//   top_left / top_right        top shell, printed face down, joined on a 45 degree scarf at top_split_x
//   bottom_left / bottom_right  bottom shell, printed feet down, joined the same way at bottom_split_x
// The two splits are staggered so each shell bridges the other's joint.
//
// Fixings: 4x M3 screws from underneath, through the bottom bosses, the PCB/plate case holes
// and into heat-set inserts in the top shell's columns.  They clamp the plate and PCB between
// the two shells, like the original's case screws.
//
// Render one part:  openscad -o top_left.stl -D 'part="top_left"' a1000_case.scad

part = "assembly"; // ["assembly","top","bottom","top_left","top_right","bottom_left","bottom_right"]
show = ["top", "bottom", "board"];  // what the assembly view includes
explode = 0;                        // lift the top shell this far in the assembly view

/* ---------------------------------------------------------------- parameters */

// Shell
wall          = 2.6;    // front, back and end walls.  The groove leaves wall - groove_d at the parting line.
top_skin      = 2.5;    // top shell thickness
floor_t       = 2.5;    // bottom shell thickness
label_skin    = 1.6;    // material left under the sloped label recess
print_safe    = true;   // stop the rounded edges at 45 degrees and finish with a chamfer, so both
                        // shells print without supports.  false = the full round.

// Board stack.  The model shows the plate at z = 0.8 (the floor of its key wells); the rest is assumed.
plate_top_z   = 0.8;    // plate top surface
plate_t       = 1.2;    // 1.2 mm FR4 plate (version 1); the original steel plate is 1.25
plate_to_pcb  = 5.0;    // plate top -> PCB top.  NOT MEASURED: depends on the Mitsumi switches.
pcb_t         = 1.6;

// Key wells: a skirt round each opening, down to just above the plate, as in the original
skirt_t       = 1.2;
skirt_gap     = 0.3;    // skirt bottom -> plate top

// Shell joint: a tongue on the bottom shell that drops inside the top shell's walls
tongue_t      = 1.2;
tongue_h      = 2.5;
tongue_clear  = 0.2;

// Screws and bosses
boss_d        = 11;     // bottom boss under the PCB / plate tab
spigot_d      = 7.0;    // passes up through the 7.5 mm case holes in the PCB and plate
squeeze       = 0.2;    // spigot stops this far below the plate top, so the screws clamp the stack
column_d      = 10;     // top shell column that lands on the plate
insert_d      = 4.0;    // M3 heat-set insert (2.6 to self-tap instead)
insert_depth  = 5.0;
screw_clear_d = 3.4;
cbore_d       = 6.5;    // M3 pan/button head
cbore_depth   = 3.0;

// Printing splits: 45 degree scarf joints, glued
top_split_x    = 200;
bottom_split_x = 185;

// 4P4C (handset) jack in the back wall: the original's coiled cable plugs in here.  The notch
// in the original bottom case is at about x 83-97 (scaled from a photo).  The jack sits on the
// floor against the back wall, held between ribs; J1 is wired to it.  Jack sizes are typical
// values, NOT MEASURED: check them against the jack you use.
jack_x        = 90;     // centre of the jack
jack_body     = [11.5, 10.0, 11.0];   // jack body width (x), depth (y), height (z)
jack_plug     = [8.4, 7.2];           // plug opening in the back wall, width x height (the notch runs on up to the parting line)
rib_t         = 1.6;    // ribs that hold the jack
rib_clear     = 0.2;

feet          = "printed";  // ["printed","none"]: the model shows four square feet

$fn = 48;

/* ------------------------------------------------ geometry from the scale model */

// Outside of the case.  The front and back edges are rounded, the ends are square.
CX0 = -8.0;   CX1 = 397.7;
CY0 = -8.15;  CY1 = 149.75;
CZ  = 11.8;            // top at +CZ, bottom at -CZ
edge_r = 5.9;          // front and back edge radius

// Parting groove round the middle (the model steps it; one 1.6 x 1.2 groove is close enough)
groove_h = 1.6;
groove_d = 1.2;

// Key openings.  One stepped opening for the main block and top row, one for the keypad.
main_open = [[2.92, 120.13], [25.1, 120.13], [25.1, 101.1], [31.47, 101.1], [31.47, 120.13],
             [153.6, 120.13], [153.6, 101.1], [159.97, 101.1], [159.97, 120.13],
             [282.1, 120.13], [282.1, 101.1], [288.47, 101.1], [288.47, 120.13],
             [310.65, 120.13], [310.65, 43.99], [320.17, 43.99], [320.17, 21.8], [310.65, 21.8],
             [310.65, 2.77], [288.47, 2.77], [288.47, 21.8], [267.82, 21.8], [267.82, 2.77],
             [26.71, 2.77], [26.71, 21.8], [2.92, 21.8]];
pad_open  = [[326.54, 2.77], [386.8, 2.77], [386.8, 101.1], [326.54, 101.1]];

// Label recess behind the keys: its floor slopes up towards the back
LBL = [31.47, 125.9, 282.1, 143.35];   // x0, y0, x1, y1
lbl_z0 = 8.34;   // floor height at the front edge
lbl_z1 = 10.27;  // and at the back edge

// Badge recess, rear right (the original carries the Amiga logo here)
badge_c = [379.05, 131.05];
badge_w = 15.5;
badge_r = 1.5;
badge_depth = 0.5;

// Label recess under the case
BLBL = [79.94, 52.81, 149.89, 104.27];
blbl_depth = 0.3;

// Feet: 19 mm square, 2.25 mm tall
foot_w = 19;
foot_h = 2.25;
foot_c = [[36.47, 7.84], [353.25, 7.84], [36.47, 108.77], [353.25, 108.77]];

/* ------------------------------------------------ geometry from the PCB (docs/measurements.md) */

// PCB outline: the back edge steps, the front edge is straight
pcb_outline = [[0, 0], [389.25, 0], [389.25, 119.60], [342.95, 119.60], [342.95, 144.99],
               [103.55, 144.99], [103.55, 134.90], [71.10, 134.90], [71.10, 121.36], [0, 121.36]];
// Switch plate: 2 mm wider than the PCB each side, with a tab on the back edge
plate_outline = [[-2.0, 0.46], [391.25, 0.46], [391.25, 121.36], [66.8, 121.36], [66.8, 146.36],
                 [48.8, 146.36], [48.8, 121.36], [-2.0, 121.36]];

// Case screws: the PCB's three 7.5 mm case holes (through the plate too) and the plate tab's hole
pcb_screws = [[16.7, 15.3], [318.14, 15.23], [375.64, 110.28]];
tab_screw  = [57.8, 133.86];
tab_x      = [48.8, 66.8];

// The tallest parts on the controller strip: [ref, x, y, footprint w, d, height above the PCB]
// Y1 lies flat, its can towards the front (the Crystal_HC49-U_Horizontal footprint)
tall_parts = [["Y1 crystal (HC-49/U, laid flat)", 247.25, 129.65, 10.9, 13.0, 5.0],
              ["C8 47 uF electrolytic",          174.6, 136.85, 5.0, 5.0, 11.0],
              ["U1 6500/1 in a socket",          319.6, 138.15, 52.0, 15.5, 8.5]];

/* ---------------------------------------------------------------- derived */

plate_bot_z = plate_top_z - plate_t;
pcb_top_z   = plate_top_z - plate_to_pcb;
pcb_bot_z   = pcb_top_z - pcb_t;
ceil_z      = CZ - top_skin;           // inside of the top shell
floor_z     = -CZ + floor_t;           // inside of the bottom shell
IX0 = CX0 + wall; IX1 = CX1 - wall;    // cavity
IY0 = CY0 + wall; IY1 = CY1 - wall;

function lbl_floor(y) = lbl_z0 + (y - LBL[1]) * (lbl_z1 - lbl_z0) / (LBL[3] - LBL[1]);
function in_lbl(x, y, m = 0) = x > LBL[0] - m && x < LBL[2] + m && y > LBL[1] - m && y < LBL[3] + m;
// inside of the top shell at (x, y): lower under the label recess
function ceiling_at(x, y) = in_lbl(x, y, label_skin) ? lbl_floor(min(max(y, LBL[1]), LBL[3])) - label_skin : ceil_z;

echo(str("case: ", CX1 - CX0, " x ", CY1 - CY0, " x ", 2 * CZ, " mm (", 2 * CZ + (feet == "printed" ? foot_h : 0), " on its feet)"));
echo(str("plate top ", plate_top_z, ", PCB top ", pcb_top_z, ", under the PCB ", pcb_bot_z - floor_z, " mm to the floor"));
if (IY1 - jack_body[1] - rib_t < 134.90) echo(str("WARNING: the jack pocket reaches y ", IY1 - jack_body[1] - rib_t,
                                                  ", past the PCB's back edge at 134.90 there"));
for (p = tall_parts) {
    room = ceiling_at(p[1], p[2]) - pcb_top_z;
    echo(str(room < p[5] ? "WARNING: " : "", p[0], ": ", room, " mm above the PCB, part is ", p[5]));
}
echo(str("top halves ", top_split_x + CZ - CX0, " / ", CX1 - top_split_x,
         "   bottom halves ", bottom_split_x - CX0, " / ", CX1 - bottom_split_x + CZ));

/* ---------------------------------------------------------------- helpers */

module rrect(x0, y0, x1, y1, r) {
    translate([x0 + r, y0 + r]) offset(r = r) square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]);
}

// profile2d: the case cross-section in (y, z): a rectangle with the four long edges rounded.
// With print_safe, each round stops at 45 degrees and runs on to the flat face as a chamfer,
// so the shells print face down without supports.
function corner_pts(cy, cz, sy, sz) =
    let(a_end = print_safe ? 45 : 90,
        arc = [for (a = [0 : 5 : a_end]) [cy + sy * edge_r * cos(a), cz + sz * edge_r * sin(a)]],
        p = arc[len(arc) - 1],
        d = CZ - abs(p[1]))
    print_safe ? concat(arc, [[p[0] - sy * d, sz * CZ]]) : arc;
module profile2d() {
    hull() for (sy = [-1, 1], sz = [-1, 1])
        polygon(concat([[sy < 0 ? CY0 + edge_r : CY1 - edge_r, sz * (CZ - edge_r)]],
                       corner_pts(sy < 0 ? CY0 + edge_r : CY1 - edge_r, sz * (CZ - edge_r), sy, sz)));
}

// shell_solid: the profile run the length of the case, minus the groove
module shell_solid() {
    difference() {
        translate([CX0, 0, 0]) rotate([90, 0, 90]) linear_extrude(CX1 - CX0) profile2d();
        difference() {
            translate([CX0 - 1, CY0 - 1, -groove_h / 2]) cube([CX1 - CX0 + 2, CY1 - CY0 + 2, groove_h]);
            translate([CX0 + groove_d, CY0 + groove_d, -groove_h]) cube([CX1 - CX0 - 2 * groove_d, CY1 - CY0 - 2 * groove_d, 2 * groove_h]);
        }
    }
}

// openings2d: the key openings, grown by g
module openings2d(g = 0) { offset(delta = g) { polygon(main_open); polygon(pad_open); } }

// left_of: the half-space left of a 45 degree scarf through (x, z0); it leans right as z moves
// away from z0, so the part that starts on the bed grows outward at 45 degrees as it prints.
module left_of(x, z0, dir) {
    multmatrix([[1, 0, dir, x - dir * z0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        translate([-1000, -500, -100]) cube([1000, 1000, 200]);
}

/* ---------------------------------------------------------------- top shell */

module top_shell() {
    difference() {
        union() {
            difference() {
                intersection() {
                    shell_solid();
                    translate([CX0 - 1, CY0 - 1, 0]) cube([CX1 - CX0 + 2, CY1 - CY0 + 2, CZ + 1]);
                }
                translate([IX0, IY0, -1]) cube([IX1 - IX0, IY1 - IY0, ceil_z + 1]);
            }
            // key well skirts, down to just above the plate
            translate([0, 0, plate_top_z + skirt_gap]) linear_extrude(ceil_z - plate_top_z - skirt_gap + 0.01)
                difference() { openings2d(skirt_t); openings2d(); }
            // backing under the sloped label recess
            hull() for (y = [LBL[1] - label_skin, LBL[3] + label_skin]) {
                z = lbl_floor(min(max(y, LBL[1]), LBL[3])) - label_skin;
                translate([LBL[0] - label_skin, y - 0.01, z]) cube([LBL[2] - LBL[0] + 2 * label_skin, 0.02, CZ - z - 0.5]);
            }
            // screw columns, landing on the plate
            for (p = concat(pcb_screws, [tab_screw])) translate([p[0], p[1], plate_top_z])
                cylinder(d = column_d, h = ceiling_at(p[0], p[1]) - plate_top_z + 0.01);
        }
        translate([0, 0, -1]) linear_extrude(CZ + 2) openings2d();
        // sloped label recess
        hull() for (y = [LBL[1], LBL[3]])
            translate([LBL[0], y - 0.01, lbl_floor(y)]) cube([LBL[2] - LBL[0], 0.02, CZ]);
        // badge recess
        translate([0, 0, CZ - badge_depth]) linear_extrude(1)
            rrect(badge_c[0] - badge_w / 2, badge_c[1] - badge_w / 2, badge_c[0] + badge_w / 2, badge_c[1] + badge_w / 2, badge_r);
        // heat-set inserts
        for (p = concat(pcb_screws, [tab_screw])) translate([p[0], p[1], plate_top_z - 0.01])
            cylinder(d = insert_d, h = insert_depth);
    }
}

/* ---------------------------------------------------------------- bottom shell */

module bottom_shell() {
    difference() {
        union() {
            difference() {
                intersection() {
                    shell_solid();
                    translate([CX0 - 1, CY0 - 1, -CZ - 1]) cube([CX1 - CX0 + 2, CY1 - CY0 + 2, CZ + 1]);
                }
                translate([IX0, IY0, floor_z]) cube([IX1 - IX0, IY1 - IY0, CZ]);
            }
            // tongue that locates the top shell; gapped round the plate tab
            difference() {
                translate([IX0 + tongue_clear, IY0 + tongue_clear, -0.01])
                    cube([IX1 - IX0 - 2 * tongue_clear, IY1 - IY0 - 2 * tongue_clear, tongue_h]);
                translate([IX0 + tongue_clear + tongue_t, IY0 + tongue_clear + tongue_t, -1])
                    cube([IX1 - IX0 - 2 * (tongue_clear + tongue_t), IY1 - IY0 - 2 * (tongue_clear + tongue_t), tongue_h + 2]);
                translate([tab_x[0] - 2, IY1 - 5, -1]) cube([tab_x[1] - tab_x[0] + 4, 10, tongue_h + 2]);
                translate([jack_x - jack_body[0] / 2 - rib_clear, IY1 - 5, -1]) cube([jack_body[0] + 2 * rib_clear, 10, tongue_h + 2]);
            }
            jack_ribs();
            // bosses under the PCB, and under the plate tab, with spigots up through the holes
            for (p = pcb_screws) translate([p[0], p[1], floor_z - 0.01]) {
                cylinder(d = boss_d, h = pcb_bot_z - floor_z);
                cylinder(d = spigot_d, h = plate_top_z - squeeze - floor_z);
            }
            translate([tab_screw[0], tab_screw[1], floor_z - 0.01]) {
                cylinder(d = boss_d, h = plate_bot_z - floor_z);
                cylinder(d = spigot_d, h = plate_top_z - squeeze - floor_z);
            }
            if (feet == "printed") for (c = foot_c) translate([0, 0, -CZ - foot_h])
                linear_extrude(foot_h + 0.01) rrect(c[0] - foot_w / 2, c[1] - foot_w / 2, c[0] + foot_w / 2, c[1] + foot_w / 2, 2);
        }
        // screws from underneath
        for (p = concat(pcb_screws, [tab_screw])) translate([p[0], p[1], -CZ - 1]) {
            cylinder(d = screw_clear_d, h = 2 * CZ, $fn = 24);
            cylinder(d = cbore_d, h = cbore_depth + 1);
        }
        // label recess underneath
        translate([0, 0, -CZ - 1]) linear_extrude(1 + blbl_depth) rrect(BLBL[0], BLBL[1], BLBL[2], BLBL[3], 2);
        // plug opening, centred on the jack body.  It runs up to the parting line as an open
        // notch, as on the original, so no thin sliver of wall is left above it; the top shell closes it.
        translate([jack_x - jack_plug[0] / 2, IY1 - 1, floor_z + (jack_body[2] - jack_plug[1]) / 2])
            cube([jack_plug[0], wall + 2, CZ]);
    }
}

// jack_ribs: two side ribs and a back stop on the floor; the jack drops in from above
module jack_ribs() {
    w = jack_body[0] + 2 * rib_clear;
    d = jack_body[1] + rib_clear;
    h = jack_body[2] - 2;
    for (x = [jack_x - w / 2 - rib_t, jack_x + w / 2]) translate([x, IY1 - d - rib_t, floor_z - 0.01]) cube([rib_t, d + rib_t + 0.01, h]);
    translate([jack_x - w / 2, IY1 - d - rib_t, floor_z - 0.01]) cube([w, rib_t, h / 2]);
}

/* ---------------------------------------------------------------- reference board */

module board() {
    color("darkgreen", 0.8) translate([0, 0, pcb_bot_z]) linear_extrude(pcb_t) polygon(pcb_outline);
    color("dimgray", 0.8) translate([0, 0, plate_bot_z]) linear_extrude(plate_t) polygon(plate_outline);
    color("silver", 0.8) translate([jack_x - jack_body[0] / 2, IY1 - jack_body[1], floor_z]) cube(jack_body);
    color("orange", 0.8) for (p = tall_parts) translate([p[1] - p[3] / 2, p[2] - p[4] / 2, pcb_top_z]) cube([p[3], p[4], p[5]]);
}

/* ---------------------------------------------------------------- output */

// Print orientation: top shell face down, bottom shell feet down, both at the origin.
module print_top()    { translate([-CX0, -CY0, CZ]) mirror([0, 0, 1]) children(); }
module print_bottom() { translate([-CX0, -CY0, CZ + (feet == "printed" ? foot_h : 0)]) children(); }

// The scarfs lean so that each piece only grows outward as it prints.
module top_piece(left)    { intersection() { top_shell();    if (left) left_of(top_split_x, CZ, -1);     else difference() { cube(2000, center = true); left_of(top_split_x, CZ, -1); } } }
module bottom_piece(left) { intersection() { bottom_shell(); if (left) left_of(bottom_split_x, -CZ, -1); else difference() { cube(2000, center = true); left_of(bottom_split_x, -CZ, -1); } } }

if (part == "assembly") {
    if (search(["top"], show)[0] != []) color("#e8e0d0") translate([0, 0, explode]) top_shell();
    if (search(["bottom"], show)[0] != []) color("#d8d0c0") bottom_shell();
    if (search(["board"], show)[0] != []) board();
}
if (part == "top")          print_top() top_shell();
if (part == "bottom")       print_bottom() bottom_shell();
if (part == "top_left")     print_top() top_piece(true);
if (part == "top_right")    print_top() top_piece(false);
if (part == "bottom_left")  print_bottom() bottom_piece(true);
if (part == "bottom_right") print_bottom() bottom_piece(false);

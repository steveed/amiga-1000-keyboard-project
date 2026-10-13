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
//   bottom_left / bottom_right  bottom shell, printed base down, joined the same way at bottom_split_x
// The two splits are staggered so each shell bridges the other's joint.
// Or two parts on a big enough bed (split = false): top and bottom, each in one piece.
//
// Fixings: 4x M3 screws from underneath, through the bottom bosses, the PCB/plate case holes
// and into heat-set inserts in the top shell's columns, like the original's case screws.  Snaps
// along the front and back hold the long edges between them, and filament dowels line up each
// scarf joint for gluing.
//
// Render one part:  openscad -o top_left.stl -D 'part="top_left"' a1000_case.scad

part = "assembly"; // ["assembly","top","bottom","top_left","top_right","bottom_left","bottom_right","jack_test_bottom","jack_test_top","joint_test_top_left","joint_test_top_right","joint_test_bottom_left","joint_test_bottom_right"]
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

// Key wells: a skirt round each opening, as in the original
skirt_t       = 1.2;
skirt_h       = 8.65;   // case top -> skirt bottom, measured on an original

// Shell joint: a tongue on the bottom shell that drops inside the top shell's walls
tongue_t      = 1.2;
tongue_h      = 3.8;    // as on the original
tongue_clear  = 0.2;

// Screws and bosses
boss_d        = 11;     // bottom boss under the PCB / plate tab
pcb_boss_h    = 1.0;    // under the PCB the boss is a 1 mm shoulder, as on the original, so it never props the board up
spigot_d      = 7.0;    // passes up through the 7.5 mm case holes in the PCB and plate
squeeze       = 0.2;    // spigot stops this far below the plate top, so the screws clamp the stack
column_d      = 10;     // top shell screw column; it stops level with the skirts, as on the original
insert_d      = 4.0;    // M3 heat-set insert (2.6 to self-tap instead)
insert_depth  = 5.0;
screw_clear_d = 3.4;
cbore_d       = 6.5;    // M3 pan/button head
cbore_depth   = 3.0;

// Printing splits: 45 degree scarf joints, glued.  split = false prints each shell in one piece, with no
// dowels, for a bed that takes 406 x 158 mm (or about 400 mm square, laid diagonally).
split          = true;
top_split_x    = 200;
bottom_split_x = 185;

// Dowels across each scarf, so the halves can't slide while the glue sets: a block inside the wall
// at the front and the back of each joint, split with it, and a hole along x through both halves
// for a length of 1.75 mm filament.  [y0, y1, z0, z1, hole y, hole z]; the block is centred on
// where the scarf crosses the hole.
dowel_d       = 2.0;    // hole, for 1.75 mm filament
dowel_len     = 20;     // 10 mm into each half
dowel_block_l = 24;     // block length along x
top_dowels    = [[-5.55, 1.57, 4.1, 9.31, -2.0, 6.7],       // front: wall to skirt, above the tongue
                 [142.5, 147.15, 4.5, 9.31, 144.8, 6.9]];   // back: behind the label recess, above the parts
bottom_dowels = [[-4.16, -0.3, -9.31, 0, -2.6, -4.5],       // front: in front of the PCB
                 [142.8, 145.76, -3.6, 3.8, 145.0, 0.0]];   // back: over the PCB's back edge, into the tongue

// Snaps between the shells, front and back, to hold the long edges down between the four screws.
// An arm hangs from the top shell just inside the tongue, and its hook catches a pocket in the bottom
// shell's wall below the parting line.  The catch face is sloped so the case still comes apart.
snap_x        = [[110, 255, 385], [150, 265, 385]];          // front, back
snap_w        = 10;     // along x
snap_t        = 1.6;    // arm thickness
snap_clear    = 0.2;    // arm to the tongue and wall
snap_hook     = 0.8;    // hook depth; it catches snap_hook - snap_clear
snap_hook_h   = [-3.0, -1.4];                // hook bottom (arm end) and catch, in z
snap_lead     = 0.7;    // height of the lead-in ramp at the bottom of the hook
snap_catch_a  = 30;     // catch face, degrees down from flat (0 = permanent)
snap_pocket_c = 0.15;   // pocket clearance round the hook

// 4P4C (handset) jack in the back wall: the original's coiled cable plugs in here.  The jack sits
// on the floor in an open-topped box, as on the original; J1 is wired to it.  The jack:
// a body behind the back wall, and at its right end a nose as deep as the wall that sits in the opening.
jack_size     = [22, 10.5, 13.5];     // jack body: length (x), depth behind the back wall (y), height; from a test fit
jack_open     = 15.5;   // plug opening in the back wall (the jack's nose is 15.4): from the floor up, and on in
                        // the top shell to the top of the jack
jack_right    = 101.55; // right side of the opening, and so of the jack
jack_clear    = 0.3;    // room round the jack in its box
jack_box_t    = 1.3;    // wall thickness of the box and its stop
jack_stop     = [3.5, 2.2];           // short wall that fits a slot in the jack: length left from the box's right wall,
                                      // and gap to the back wall.  It runs from the floor to the parting line.
jack_wires    = [8.0, 2.5];           // wire cutout in the box's front wall, opposite the stop: width from the inside of the
                                      // left wall, and wall left under it.  From photos, checked in a test fit.

// Which jack: "nose" is the one above.  "616e" is the common wired 616E (KLS12-199, HWS8282), a plain box
// with the plug opening in its face.  It stands on the floor centred in the notch, its face against the back
// of a filler that closes the notch except for a hole for the plug, so the outside still looks like the original.
jack_type     = "nose"; // ["nose", "616e"]
j616_size     = [11.4, 10.2, 17.42];  // width over its side ridge (x), depth (y), height: the larger of the KLS
                                      // and HWS drawings
j616_hole     = [9.0, 8.5];           // plug hole in the filler: width (centred on the jack), height from the floor
j616_fill     = 0.6;    // the filler stands this far in from the outside of the back wall, so the notch still shows
j616_skin     = 1.0;    // label skin left over the jack (label_skin elsewhere), for room above its 17.4 mm

// Test print: just the jack corner of each shell, to try the jack in before printing the whole case
jack_test     = [70, 120, 125];       // x0, x1, y0; it runs on to the back of the case

// Test print: a strip along the front of each shell, across both scarf joints and the snap at x 255,
// each split at its joint, to try the dowels and a snap before printing the whole case
joint_test    = [160, 262, 10];       // x0, x1, y1; it runs from the front of the case

feet          = "recessed"; // ["recessed","none"]: pockets for stick-on rubber feet where the model shows four square feet
foot_depth    = 1.0;        // pocket depth, out of the floor_t floor

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

// Feet: 19 mm square (the model's are 2.25 mm tall; here they are pockets for rubber feet)
foot_w = 19;
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
jack_x  = jack_right - jack_open / 2;                                  // centre of the plug opening
j616    = jack_type == "616e";
jack_in = j616 ? [jack_x - j616_size[0] / 2 - jack_clear, IY1 - j616_size[1] - jack_clear, jack_x + j616_size[0] / 2 + jack_clear]
               : [jack_right - jack_size[0] - jack_clear, IY1 - jack_size[1] - jack_clear, jack_right];  // inside of the jack box: x0, y0, x1
jack_notch_top = floor_z + jack_size[2] + jack_clear;                  // top of the top shell's notch, the same for both jacks

wall_in = [IY0 + tongue_clear + tongue_t, IY1 - tongue_clear - tongue_t];   // inside of the bottom shell's wall, below the parting line
function top_split_at(z)    = top_split_x - (z - CZ);       // where each scarf crosses height z
function bottom_split_at(z) = bottom_split_x - (z + CZ);
function lbl_floor(y) = lbl_z0 + (y - LBL[1]) * (lbl_z1 - lbl_z0) / (LBL[3] - LBL[1]);
function in_lbl(x, y, m = 0) = x > LBL[0] - m && x < LBL[2] + m && y > LBL[1] - m && y < LBL[3] + m;
// inside of the top shell at (x, y): lower under the label recess
function ceiling_at(x, y) = in_lbl(x, y, label_skin) ? lbl_floor(min(max(y, LBL[1]), LBL[3])) - label_skin : ceil_z;

echo(str("case: ", CX1 - CX0, " x ", CY1 - CY0, " x ", 2 * CZ, " mm, before its rubber feet"));
echo(str("plate top ", plate_top_z, ", PCB top ", pcb_top_z, ", under the PCB ", pcb_bot_z - floor_z, " mm to the floor"));
echo(str("key well skirts stop ", CZ - skirt_h - plate_top_z, " mm above the plate"));
if (CZ - skirt_h <= plate_top_z) echo("WARNING: the key well skirts reach the plate");
if (jack_in[1] - jack_box_t < 134.90) echo(str("WARNING: the jack box reaches y ", jack_in[1] - jack_box_t,
                                                  ", past the PCB's back edge at 134.90 there"));
if (j616) {
    room = lbl_floor(jack_in[1]) - j616_skin - (floor_z + j616_size[2]);
    echo(str(room < 0.2 ? "WARNING: " : "", "616E jack: ", room, " mm clear under the label recess"));
}
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
            // key well skirts
            translate([0, 0, CZ - skirt_h]) linear_extrude(skirt_h - top_skin + 0.01)
                difference() { openings2d(skirt_t); openings2d(); }
            // backing under the sloped label recess
            hull() for (y = [LBL[1] - label_skin, LBL[3] + label_skin]) {
                z = lbl_floor(min(max(y, LBL[1]), LBL[3])) - label_skin;
                translate([LBL[0] - label_skin, y - 0.01, z]) cube([LBL[2] - LBL[0] + 2 * label_skin, 0.02, CZ - z - 0.5]);
            }
            // screw columns, level with the skirts
            for (p = concat(pcb_screws, [tab_screw])) translate([p[0], p[1], CZ - skirt_h])
                cylinder(d = column_d, h = ceiling_at(p[0], p[1]) - (CZ - skirt_h) + 0.01);
            for (d = top_dowels) dowel_block(d, top_split_at(d[5]));
            for (s = [0, 1], x = snap_x[s]) snap_arm(x, s);
        }
        translate([0, 0, -1]) linear_extrude(CZ + 2) openings2d();
        // sloped label recess
        hull() for (y = [LBL[1], LBL[3]])
            translate([LBL[0], y - 0.01, lbl_floor(y)]) cube([LBL[2] - LBL[0], 0.02, CZ]);
        // badge recess
        translate([0, 0, CZ - badge_depth]) linear_extrude(1)
            rrect(badge_c[0] - badge_w / 2, badge_c[1] - badge_w / 2, badge_c[0] + badge_w / 2, badge_c[1] + badge_w / 2, badge_r);
        // heat-set inserts
        for (p = concat(pcb_screws, [tab_screw])) translate([p[0], p[1], CZ - skirt_h - 0.01])
            cylinder(d = insert_d, h = insert_depth);
        for (d = top_dowels) dowel_hole(d, top_split_at(d[5]));
        // notch over the bottom shell's plug opening, up to the top of the jack, for plug clearance
        translate([jack_x - jack_open / 2, IY1 - 1, -1])
            cube([jack_open, wall + 2, jack_notch_top + 1]);
        // room over a 616E: thin the label skin above it
        if (j616) hull() for (y = [jack_in[1], IY1]) translate([jack_in[0], y - 0.01, -1])
            cube([jack_in[2] - jack_in[0], 0.02, lbl_floor(min(y, LBL[3])) - j616_skin + 1]);
    }
    if (j616) jack_filler(0, jack_notch_top);
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
            // tongue that locates the top shell; gapped round the plate tab and the jack.  Below the
            // parting line it thickens the wall down to the floor, so it prints on something.
            difference() {
                union() {
                    translate([IX0 - 0.01, IY0 - 0.01, floor_z - 0.01])
                        cube([IX1 - IX0 + 0.02, IY1 - IY0 + 0.02, -floor_z + 0.01]);
                    translate([IX0 + tongue_clear, IY0 + tongue_clear, 0])
                        cube([IX1 - IX0 - 2 * tongue_clear, IY1 - IY0 - 2 * tongue_clear, tongue_h]);
                }
                translate([IX0 + tongue_clear + tongue_t, IY0 + tongue_clear + tongue_t, floor_z - 1])
                    cube([IX1 - IX0 - 2 * (tongue_clear + tongue_t), IY1 - IY0 - 2 * (tongue_clear + tongue_t), tongue_h + 2 - floor_z]);
                translate([tab_x[0] - 2, IY1 - 5, -1]) cube([tab_x[1] - tab_x[0] + 4, 10, tongue_h + 2]);
                translate([jack_in[0], IY1 - 5, floor_z]) cube([jack_in[2] - jack_in[0], 10, tongue_h + 1 - floor_z]);
            }
            jack_box();
            // bosses: a low shoulder under the PCB and a full-height one under the plate tab, with spigots up through the holes
            for (p = pcb_screws) translate([p[0], p[1], floor_z - 0.01]) {
                cylinder(d = boss_d, h = pcb_boss_h);
                cylinder(d = spigot_d, h = plate_top_z - squeeze - floor_z);
            }
            translate([tab_screw[0], tab_screw[1], floor_z - 0.01]) {
                cylinder(d = boss_d, h = plate_bot_z - floor_z);
                cylinder(d = spigot_d, h = plate_top_z - squeeze - floor_z);
            }
            for (d = bottom_dowels) dowel_block(d, bottom_split_at(d[5]));
        }
        for (d = bottom_dowels) dowel_hole(d, bottom_split_at(d[5]));
        for (s = [0, 1], x = snap_x[s]) snap_pocket(x, s);
        // screws from underneath
        for (p = concat(pcb_screws, [tab_screw])) translate([p[0], p[1], -CZ - 1]) {
            cylinder(d = screw_clear_d, h = 2 * CZ, $fn = 24);
            cylinder(d = cbore_d, h = cbore_depth + 1);
        }
        // pockets for stick-on rubber feet
        if (feet == "recessed") for (c = foot_c) translate([0, 0, -CZ - 1])
            linear_extrude(1 + foot_depth) rrect(c[0] - foot_w / 2, c[1] - foot_w / 2, c[0] + foot_w / 2, c[1] + foot_w / 2, 2);
        // label recess underneath
        translate([0, 0, -CZ - 1]) linear_extrude(1 + blbl_depth) rrect(BLBL[0], BLBL[1], BLBL[2], BLBL[3], 2);
        // plug opening: an open notch from the floor up to the parting line, as on the original; the top
        // shell's matching notch completes it.
        translate([jack_x - jack_open / 2, IY1 - 1, floor_z])
            cube([jack_open, wall + 2, CZ]);
    }
    if (j616) jack_filler(floor_z, 0);
}

// jack_filler: closes the plug notch between z0 and z1 in front of a 616E, short of the outside so the notch
// still shows, with a hole for the plug from the floor up
module jack_filler(z0, z1) {
    difference() {
        intersection() {
            shell_solid();
            translate([jack_x - jack_open / 2 - 0.01, IY1 - 0.01, z0 - 0.01])
                cube([jack_open + 0.02, CY1 - j616_fill - IY1 + 0.01, z1 - z0 + 0.02]);
        }
        translate([jack_x - j616_hole[0] / 2, IY1 - 1, floor_z - 1]) cube([j616_hole[0], wall + 2, j616_hole[1] + 1]);
    }
}

// jack_box: side and front walls round the jack, open on top so the jack drops in and its wires leave over
// the top or through a cutout in the front wall, and a short stop inside the right wall, as on the original,
// that holds the jack in place.  A 616E's wires leave its back near the top, over the box, and it has no slot,
// so it gets neither.
module jack_box() {
    x0 = jack_in[0]; x1 = jack_in[2]; y0 = jack_in[1]; t = jack_box_t;
    difference() {
        translate([x0 - t, y0 - t, floor_z - 0.01]) cube([x1 - x0 + 2 * t, IY1 - y0 + t, tongue_h - floor_z + 0.01]);
        translate([x0, y0, floor_z]) cube([x1 - x0, IY1 - y0 + 1, tongue_h - floor_z + 1]);
        if (!j616) translate([x0, y0 - t - 1, floor_z + jack_wires[1]]) cube([jack_wires[0], t + 2, tongue_h - floor_z]);
    }
    if (!j616) translate([x1 - jack_stop[0], IY1 - jack_stop[1] - t, floor_z - 0.01])
        cube([jack_stop[0] + 0.01, t, -floor_z + 0.01]);
}

/* ---------------------------------------------------------------- dowels and snaps */

// dowel_block / dowel_hole: d = [y0, y1, z0, z1, hole y, hole z], centred on x along the case; none when
// the shells print in one piece
module dowel_block(d, x) {
    if (split) translate([x - dowel_block_l / 2, d[0], d[2]]) cube([dowel_block_l, d[1] - d[0], d[3] - d[2]]);
}
module dowel_hole(d, x) {
    if (split) translate([x - dowel_len / 2 - 0.5, d[4], d[5]]) rotate([0, 90, 0]) cylinder(d = dowel_d, h = dowel_len + 1, $fn = 16);
}

// snap_hook2d: the hook's profile in (out, z), out measured outward from the arm's outer face.  A lead-in
// ramp at the bottom, then the full depth, then the catch face sloping back to the arm.
module snap_hook2d(g = 0) {
    z0 = snap_hook_h[0]; z1 = snap_hook_h[1]; h = snap_hook;
    offset(delta = g) polygon([[0, z0], [h, z0 + snap_lead], [h, z1], [0, z1 + h * tan(snap_catch_a)]]);
}
// in (out, z) to case (y, z) for side s (0 front, 1 back), from the arm's outer face y_face
module snap_place(s, x, y_face) {
    translate([x, y_face, 0]) rotate([90, 0, 90]) mirror([s == 0 ? 1 : 0, 0]) children();
}

// snap_arm: hangs from the top shell's ceiling just inside the tongue, hook outward
module snap_arm(x, s) {
    out  = s == 0 ? -1 : 1;
    face = wall_in[s] - out * snap_clear;                    // arm's outer face
    top  = ceiling_at(x, face) + 0.01;
    translate([x - snap_w / 2, out < 0 ? face : face - snap_t, snap_hook_h[0]])
        cube([snap_w, snap_t, top - snap_hook_h[0]]);
    snap_place(s, x - snap_w / 2, face) linear_extrude(snap_w) snap_hook2d();
}

// snap_pocket: the hook's catch, cut into the bottom shell's wall below the parting line
module snap_pocket(x, s) {
    face = wall_in[s] - (s == 0 ? -1 : 1) * snap_clear;
    snap_place(s, x - snap_w / 2 - 0.3, face) linear_extrude(snap_w + 0.6) union() {
        snap_hook2d(snap_pocket_c);
        translate([-1, snap_hook_h[0] - snap_pocket_c]) square([1.01, snap_hook_h[1] - snap_hook_h[0] + snap_hook + 2 * snap_pocket_c]);
    }
}

/* ---------------------------------------------------------------- reference board */

module board() {
    color("darkgreen", 0.8) translate([0, 0, pcb_bot_z]) linear_extrude(pcb_t) polygon(pcb_outline);
    color("dimgray", 0.8) translate([0, 0, plate_bot_z]) linear_extrude(plate_t) polygon(plate_outline);
    if (j616) color("silver", 0.8) translate([jack_x - j616_size[0] / 2, IY1 - j616_size[1], floor_z]) cube(j616_size);
    else color("silver", 0.8) translate([jack_right - jack_size[0], IY1 - jack_size[1], floor_z]) {
        cube(jack_size);
        translate([jack_size[0] - jack_open + 0.1, jack_size[1] - 0.01, 0]) cube([jack_open - 0.1, wall + 0.01, jack_size[2]]);
    }
    color("orange", 0.8) for (p = tall_parts) translate([p[1] - p[3] / 2, p[2] - p[4] / 2, pcb_top_z]) cube([p[3], p[4], p[5]]);
}

/* ---------------------------------------------------------------- output */

// Print orientation: top shell face down, bottom shell base down, both at the origin.  The top
// is turned over front to back (a rotation, not a mirror, which would print it handed wrong).
module print_top()    { translate([-CX0, CY1, CZ]) rotate([180, 0, 0]) children(); }
module print_bottom() { translate([-CX0, -CY0, CZ]) children(); }

// jack_test_region: the corner of the case round the jack, for the test prints
module jack_test_region() { translate([jack_test[0], jack_test[2], -CZ - 1]) cube([jack_test[1] - jack_test[0], CY1 - jack_test[2] + 1, 2 * CZ + 2]); }

// joint_test_region: the front strip across both joints, for the test prints
module joint_test_region() { translate([joint_test[0], CY0 - 1, -CZ - 5]) cube([joint_test[1] - joint_test[0], joint_test[2] - CY0 + 1, 2 * CZ + 10]); }

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
if (part == "jack_test_bottom") print_bottom() intersection() { bottom_shell(); jack_test_region(); }
if (part == "jack_test_top")    print_top() intersection() { top_shell(); jack_test_region(); }
if (part == "joint_test_top_left")     print_top()    intersection() { top_piece(true);     joint_test_region(); }
if (part == "joint_test_top_right")    print_top()    intersection() { top_piece(false);    joint_test_region(); }
if (part == "joint_test_bottom_left")  print_bottom() intersection() { bottom_piece(true);  joint_test_region(); }
if (part == "joint_test_bottom_right") print_bottom() intersection() { bottom_piece(false); joint_test_region(); }

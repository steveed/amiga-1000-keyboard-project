// a1000_keycaps.scad
//
// Keycaps for the rev 2 board (Cherry MX) in the A1000's sizes, for the keys an off-the-shelf MX
// set doesn't cover:
//   return     US Return, 1.25U over 2U (SW41).  The A500KB's US Return cap is 1.5U over 2.25U,
//              so it runs into HELP and UP.
//   tilde      ` ~, 1.25U (SW13)
//   backspace  1.75U (SW70)
//   tab        1.75U (SW28)
//   lshift     US left Shift, 2.5U (SW87), on a 2U stabiliser
//   rshift     right Shift, 2U (SW91), on a 2U stabiliser
// Pick one with -D 'key="tab"'.
//
// Coordinates: x right, y away from the typist, origin at the key's switch stem.  Sizes are the
// A1000's key grid, from the rev 2 board's switch positions.
//
// The profile is Cherry's (as made by GMK), with figures from KeyV2's cherry profile
// (github.com/rsheldiii/KeyV2): a height and tilt for each row, a cylindrical dish, and a top
// narrower than the skirt and shifted back.  It isn't the A1000's own sculpt.  Each key takes the
// Cherry row of the board row it sits in; Return takes the home row's, with the tilt spread over
// its two rows as KeyV2 does for tall keys.
// Print top down, the stems pointing up.  The dished top needs a little support or a raft.
//
// Render:  openscad -D 'key="tab"' -o tab_keycap.stl a1000_keycaps.scad

/* ---------------------------------------------------------------- parameters */

key              = "return";  // [return, tilde, backspace, tab, lshift, rshift]

U                = 19.05;

// Return: key grid edges, from the board, around the Return stem (x 295.13)
grid_left_top    = -13.965;  // right edge of ]   (271.64 + 9.525)
grid_left_bottom = -28.305;  // right edge of '   (257.30 + 9.525)
grid_right       =   9.89;   // left edges of HELP and UP (305.045, 304.995)
grid_back        =  19.245;  // back edge of row 2 (row centre 112.81)
grid_mid         =   0.195;  // between rows 2 and 3
grid_front       = -18.855;  // front edge of row 3 (row centre 131.86)
dummy            = [-18.73, -9.36];   // SW55 (276.40, 131.89), the Return cap's dummy switch

// The straight keys: width in U, whether they ride on a 2U stabiliser, and Cherry row.  Each stem
// is centred in its key on the board.
straight = [
    ["tilde",     1.25, false, 1],
    ["backspace", 1.75, false, 1],
    ["tab",       1.75, false, 2],
    ["lshift",    2.5,  true,  4],
    ["rshift",    2.0,  true,  4],
];
return_row       = 3;

stab             = 11.938;   // 2U stabiliser inserts, either side of the switch

// Cherry profile.  Rows count from the number row (1) to the Shift row (4).  Height is skirt bottom
// to the middle of the top, before the dish; tilt is in degrees, the front edge raised.
cherry           = [[9.8, 0], [7.45, 2.5], [6.55, 5], [7.35, 11.5]];
top_in_x         = 3.155;    // top in from the skirt, each side: 18.16 at the skirt, 11.85 at the top
top_in_y         = 1.76;     //   and 14.64 front to back
top_skew         = 2.0;      // top moved back
dish_depth       = 0.65;     // cylindrical, across the key

// Cap
gap              = 0.45;     // in from the grid at the skirt, each side (an 18.15 mm 1U cap)
wall             = 1.4;
top_t            = 1.6;      // under the bottom of the dish

// MX stem
stem_d           = 5.5;
cross_l          = 4.1;      // cross slot, each arm
cross_w          = 1.35;     // tune for the printer: the switch's cross is 4.0 x 1.17 / 1.30
cross_depth      = 3.8;
stem_drop        = 0.6;      // stem bottom above the skirt bottom, as on Cherry caps

$fn = 48;

/* ---------------------------------------------------------------- model */

row = [for (k = straight) if (k[0] == key) k];
assert(key == "return" || len(row) == 1, str("unknown key: ", key));
half   = key == "return" ? 0 : row[0][1] * U / 2;
crow   = key == "return" ? return_row : row[0][3];
height = cherry[crow - 1][0];
tilt   = cherry[crow - 1][1] / (key == "return" ? 2 : 1);    // over the key's height in U
y_mid  = key == "return" ? (grid_front + grid_back) / 2 : 0;   // the top tilts about the key's middle

// The top's plane: tilted about the key's middle, `down` below the top surface
module on_top(down = 0) {
    translate([0, y_mid, height - down]) rotate([-tilt, 0, 0]) translate([0, -y_mid, 0]) children();
}

// A part from [x0, x1] x [y0, y1] at the skirt to the tilted top, grown by `out` and with its top
// `down` lower
module part(x0, x1, y0, y1, out = 0, down = 0) {
    hull() {
        translate([x0 - out, y0 - out, 0]) cube([x1 - x0 + 2 * out, y1 - y0 + 2 * out, 0.01]);
        on_top(down) translate([x0 + top_in_x - out, y0 + top_in_y + top_skew - out, -0.01])
            cube([x1 - x0 - 2 * top_in_x + 2 * out, y1 - y0 - 2 * top_in_y + 2 * out, 0.01]);
    }
}

// Return: the L, the column the two rows share and the bottom row's extension to the left.
// The rest: a rectangle.
module shape(out = 0, down = 0) {
    if (key == "return") {
        part(grid_left_top + gap, grid_right - gap, grid_front + gap, grid_back - gap, out, down);
        part(grid_left_bottom + gap, grid_right - gap, grid_front + gap, grid_mid - gap, out, down);
    } else {
        part(-half + gap, half - gap, -U / 2 + gap, U / 2 - gap, out, down);
    }
}

// The dish: a cylinder along the key, dish_depth deep across the widest part of the top
dish_x0 = key == "return" ? grid_left_bottom + gap + top_in_x : -half + gap + top_in_x;
dish_x1 = key == "return" ? grid_right - gap - top_in_x      : half - gap - top_in_x;
dish_w  = dish_x1 - dish_x0;
dish_r  = (dish_w * dish_w / 4 + dish_depth * dish_depth) / (2 * dish_depth);
module dish() {
    on_top() translate([(dish_x0 + dish_x1) / 2, 0, dish_r - dish_depth])
        rotate([90, 0, 0]) cylinder(r = dish_r, h = 4 * U, center = true, $fn = 360);
}

module stem(p) {
    translate([p[0], p[1], stem_drop]) difference() {
        cylinder(d = stem_d, h = height + 5);
        translate([0, 0, -0.01]) {
            translate([-cross_l / 2, -cross_w / 2, 0]) cube([cross_l, cross_w, cross_depth]);
            translate([-cross_w / 2, -cross_l / 2, 0]) cube([cross_w, cross_l, cross_depth]);
        }
    }
}

stems = key == "return" ? [[0, 0], [0, stab], [0, -stab], dummy]   // vertical stabiliser
      : row[0][2]       ? [[0, 0], [-stab, 0], [stab, 0]]
      :                   [[0, 0]];

difference() {
    union() {
        difference() {
            shape();
            translate([0, 0, -0.01]) shape(-wall, top_t + dish_depth);
        }
        intersection() {
            union() for (p = stems) stem(p);
            shape();
        }
    }
    dish();
}

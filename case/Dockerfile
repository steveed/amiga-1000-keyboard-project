# OpenSCAD with a virtual display, so it can export PNG previews as well as STLs.
FROM openscad/openscad:dev@sha256:6c1a07342e37afcd7e360d1cfa98d0e1cad3f32f2ac91a2943691e117ce4d3b4
RUN apt-get update && apt-get install -y --no-install-recommends xvfb xauth && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["xvfb-run", "-a", "openscad"]

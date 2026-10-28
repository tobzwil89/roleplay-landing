# Baut die Szene „Das Tor erwacht“ in Blender und rendert Einzelbilder.
# Alles entsteht aus Code, keine fremden Modelle oder Texturen.
#
# Aufruf (aus dem Projektordner):
#   blender -b --factory-startup -P blender/scene.py -- --fmt 16x9 --frames 45,140,240,340 --pct 50 --out blender/stills
#   --fmt     16x9 oder 9x16
#   --frames  einzelne Bilder (45,140) oder Bereich (1-390)
#   --pct     Auflösung in Prozent (50 = halbe Größe, schneller)
#   --out     Ordner für die PNGs; vorhandene Bilder werden übersprungen (Abbruch und Fortsetzen jederzeit möglich)
import bpy, bmesh, math, random, sys, os, argparse
from mathutils import Vector, noise

FPS = 30
TOTAL = 390  # 13 s
# Einstellungen: (erstes Bild, letztes Bild)
SHOTS = {'totale': (1, 90), 'fahrt': (91, 195), 'nah': (196, 285), 'ausbruch': (286, 390)}

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--fmt', default='16x9')
ap.add_argument('--frames', default='45')
ap.add_argument('--pct', type=int, default=50)
ap.add_argument('--out', default='blender/stills')
ap.add_argument('--samples', type=int, default=48)
ap.add_argument('--save', action='store_true')  # zusätzlich blender/szene.blend speichern (zum Ansehen in Blender)
args = ap.parse_args(argv)
PORTRAIT = args.fmt == '9x16'

random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, TOTAL

GOLD = (1.0, 0.62, 0.25)
BLUE = (0.35, 0.42, 1.0)


# ---------- Hilfsfunktionen ----------

def material(name, color=(0.05, 0.05, 0.06), rough=0.9, emit=None, strength=0.0, bump=0.0, scale=3.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1)
        bsdf.inputs['Emission Strength'].default_value = strength
    if bump:
        # Stein: Rauschen als Unebenheit und leichte Farbschwankung
        tex = nt.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        tex.inputs['Detail'].default_value = 12
        b = nt.nodes.new('ShaderNodeBump')
        b.inputs['Strength'].default_value = bump
        nt.links.new(tex.outputs['Fac'], b.inputs['Height'])
        nt.links.new(b.outputs['Normal'], bsdf.inputs['Normal'])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.inputs['A'].default_value = (*color, 1)
        mix.inputs['B'].default_value = (color[0] * 2.2, color[1] * 2.1, color[2] * 2.0, 1)
        nt.links.new(tex.outputs['Fac'], mix.inputs['Factor'])
        nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    return m


def link(obj, mat=None):
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def mesh_obj(name, bm, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me), mat)


def rock(name, loc, size, mat, seed, rough=0.45):
    """Felsbrocken: Ikosaeder, mit Rauschen verbeult."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    off = Vector((seed * 13.1, seed * 7.3, seed * 3.7))
    for v in bm.verts:
        n = noise.fractal(v.co * 1.3 + off, 0.6, 2.0, 5)
        v.co *= 1 + rough * n
    o = mesh_obj(name, bm, mat)
    o.location = loc
    o.scale = size
    o.rotation_euler = (random.random(), random.random(), random.random() * 6)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def key(obj, path, frames_values, interp='BEZIER'):
    """Setzt Schlüsselbilder: frames_values = [(bild, wert), ...]."""
    for f, v in frames_values:
        setattr(obj, path, v)
        obj.keyframe_insert(path, frame=f)
    if obj.animation_data and interp != 'BEZIER':
        for fc in action_fcurves(obj):
            for k in fc.keyframe_points:
                k.interpolation = interp


def action_fcurves(idblock):
    """F-Kurven einer Animation (Blender 5 legt sie in Ebenen und Streifen ab)."""
    act = idblock.animation_data.action
    if hasattr(act, 'fcurves'):
        return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def arch_profile(width, spring, n=24):
    """Umriss eines Spitzbogens (x, z): senkrechte Seiten bis `spring`, darüber zwei Kreisbögen."""
    w = width / 2
    r = width * 0.85  # Bogenradius > halbe Breite gibt die Spitze
    pts = [(-w, 0), (w, 0), (w, spring)]
    # rechter Bogen: Mittelpunkt links bei (w - r, spring)
    cx = w - r
    top = math.acos(-cx / r)
    for i in range(1, n + 1):
        a = top * i / n
        pts.append((cx + r * math.cos(a), spring + r * math.sin(a)))
    apex_z = pts[-1][1]
    for x, z in reversed(pts[3:-1]):
        pts.append((-x, z))
    pts.append((-w, spring))
    return pts, apex_z


def prism(name, pts, y0, y1, mat=None):
    """Zieht einen Umriss (x, z) in Tiefe y0..y1."""
    bm = bmesh.new()
    front = [bm.verts.new((x, y0, z)) for x, z in pts]
    back = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(list(reversed(front)))
    bm.faces.new(back)
    k = len(pts)
    for i in range(k):
        bm.faces.new((front[i], front[(i + 1) % k], back[(i + 1) % k], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # Flächen nach außen drehen, sonst schneidet das Boolean falsch
    return mesh_obj(name, bm, mat)


# ---------- Materialien ----------

stone = material('Stein', (0.045, 0.043, 0.05), 0.85, bump=0.6, scale=4)
rockmat = material('Fels', (0.03, 0.03, 0.036), 0.9, bump=0.9, scale=1.5)
ground_m = material('Boden', (0.022, 0.021, 0.026), 0.95, bump=0.5, scale=8)
wall_m = material('Mauer', (0.05, 0.047, 0.055), 0.85)
nt = wall_m.node_tree
brick = nt.nodes.new('ShaderNodeTexBrick')
brick.inputs['Scale'].default_value = 0.6
brick.inputs['Mortar Size'].default_value = 0.03
brick.inputs['Color1'].default_value = (1, 1, 1, 1)
brick.inputs['Color2'].default_value = (0.7, 0.7, 0.7, 1)
brick.inputs['Mortar'].default_value = (0, 0, 0, 1)
tc_w = nt.nodes.new('ShaderNodeTexCoord')
wn_ = nt.nodes.new('ShaderNodeTexNoise')
wn_.inputs['Scale'].default_value = 3
wn_.inputs['Detail'].default_value = 10
add_w = nt.nodes.new('ShaderNodeMath')
add_w.operation = 'MULTIPLY_ADD'
add_w.inputs[1].default_value = 0.3
bmp = nt.nodes.new('ShaderNodeBump')
bmp.inputs['Strength'].default_value = 0.8
# Ziegel liegen in der x-z-Ebene der Wand
swz = nt.nodes.new('ShaderNodeMapping')
swz.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
nt.links.new(tc_w.outputs['Object'], swz.inputs['Vector'])
nt.links.new(swz.outputs['Vector'], brick.inputs['Vector'])
nt.links.new(wn_.outputs['Fac'], add_w.inputs[0])
nt.links.new(brick.outputs['Color'], add_w.inputs[2])
nt.links.new(add_w.outputs[0], bmp.inputs['Height'])
nt.links.new(bmp.outputs['Normal'], nt.nodes['Principled BSDF'].inputs['Normal'])
cloth = material('Umhang', (0.02, 0.018, 0.022), 0.8)
wood = material('Stab', (0.04, 0.025, 0.015), 0.6)
crystal = material('Kristall', (0.2, 0.3, 1.0), 0.2, emit=(0.5, 0.6, 1.0), strength=20)
spark_m = material('Funke', (1, 0.5, 0.1), 1.0, emit=(1.0, 0.45, 0.12), strength=60)

# Tor: Runen als leuchtende Risse (Voronoi-Kanten), Stärke wird animiert
door_m = material('Torfluegel', (0.03, 0.028, 0.03), 0.6)
nt = door_m.node_tree
vor = nt.nodes.new('ShaderNodeTexVoronoi')
vor.feature = 'DISTANCE_TO_EDGE'
vor.inputs['Scale'].default_value = 2.2
geo_r = nt.nodes.new('ShaderNodeNewGeometry')
dist = nt.nodes.new('ShaderNodeTexNoise')
dist.inputs['Scale'].default_value = 2.0
dist.inputs['Distortion'].default_value = 0.0
mixv = nt.nodes.new('ShaderNodeMix')
mixv.data_type = 'VECTOR'
mixv.inputs['Factor'].default_value = 0.15
nt.links.new(geo_r.outputs['Position'], mixv.inputs['A'])
nt.links.new(dist.outputs['Color'], mixv.inputs['B'])
nt.links.new(mixv.outputs['Result'], vor.inputs['Vector'])
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
ramp.color_ramp.elements[1].position = 0.018
ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
rune_strength = nt.nodes.new('ShaderNodeMath')
rune_strength.operation = 'MULTIPLY'
nt.links.new(vor.outputs['Distance'], ramp.inputs['Fac'])
mask = nt.nodes.new('ShaderNodeTexNoise')
mask.inputs['Scale'].default_value = 1.1
mramp = nt.nodes.new('ShaderNodeMapRange')
mramp.inputs['From Min'].default_value = 0.5
mramp.inputs['From Max'].default_value = 0.6
nt.links.new(geo_r.outputs['Position'], mask.inputs['Vector'])
nt.links.new(mask.outputs['Fac'], mramp.inputs['Value'])
cracks = nt.nodes.new('ShaderNodeMath')
cracks.operation = 'MULTIPLY'
nt.links.new(ramp.outputs['Color'], cracks.inputs[0])
nt.links.new(mramp.outputs['Result'], cracks.inputs[1])
# Siegel: Ring um die Tormitte (Abstand von x = 0, z = PLAT + 3)
center = nt.nodes.new('ShaderNodeVectorMath')
center.operation = 'DISTANCE'
center.inputs[1].default_value = (0, 0.4, 1.6 + 3.0)
sep_r = nt.nodes.new('ShaderNodeSeparateXYZ')
comb_r = nt.nodes.new('ShaderNodeCombineXYZ')
nt.links.new(geo_r.outputs['Position'], sep_r.inputs[0])
nt.links.new(sep_r.outputs['X'], comb_r.inputs['X'])
nt.links.new(sep_r.outputs['Z'], comb_r.inputs['Z'])
comb_r.inputs['Y'].default_value = 0.4
nt.links.new(comb_r.outputs[0], center.inputs[0])
ring = nt.nodes.new('ShaderNodeMapRange')  # zwei Ringe bei 1,0 m und 1,25 m
ring2 = nt.nodes.new('ShaderNodeMapRange')
for rn, rad in ((ring, 1.0), (ring2, 1.25)):
    absd = nt.nodes.new('ShaderNodeMath')
    absd.operation = 'SUBTRACT'
    absd.inputs[1].default_value = rad
    ab = nt.nodes.new('ShaderNodeMath')
    ab.operation = 'ABSOLUTE'
    nt.links.new(center.outputs['Value'], absd.inputs[0])
    nt.links.new(absd.outputs[0], ab.inputs[0])
    rn.inputs['From Min'].default_value = 0.025
    rn.inputs['From Max'].default_value = 0.0
    nt.links.new(ab.outputs[0], rn.inputs['Value'])
both = nt.nodes.new('ShaderNodeMath')
both.operation = 'MAXIMUM'
nt.links.new(ring.outputs['Result'], both.inputs[0])
nt.links.new(ring2.outputs['Result'], both.inputs[1])
allr = nt.nodes.new('ShaderNodeMath')
allr.operation = 'MAXIMUM'
nt.links.new(cracks.outputs[0], allr.inputs[0])
nt.links.new(both.outputs[0], allr.inputs[1])
nt.links.new(allr.outputs[0], rune_strength.inputs[0])
bsdf = nt.nodes['Principled BSDF']
bsdf.inputs['Emission Color'].default_value = (*GOLD, 1)
nt.links.new(rune_strength.outputs[0], bsdf.inputs['Emission Strength'])
RUNE = rune_strength.inputs[1]

portal_m = material('Torlicht', (0, 0, 0), 1.0, emit=GOLD, strength=0.0)


# ---------- Gelände ----------

def ground_height(x, y):
    """Boden: flacher Weg zum Tor, links und rechts ansteigendes Geröll."""
    side = max(0.0, abs(x) - 6) ** 1.3 * 0.25
    n = noise.fractal(Vector((x * 0.05, y * 0.05, 0)), 0.5, 2.0, 6) * 2.5
    fine = noise.noise(Vector((x * 0.6, y * 0.6, 1))) * 0.15
    path_flat = min(1.0, abs(x) / 7)
    return (n * path_flat + fine + side) - 0.05

bm = bmesh.new()
N = 160
size = 240
verts = []
for j in range(N + 1):
    row = []
    for i in range(N + 1):
        x = (i / N - 0.5) * size
        y = (j / N) * size * 0.75 - size * 0.55
        row.append(bm.verts.new((x, y, ground_height(x, y))))
    verts.append(row)
for j in range(N):
    for i in range(N):
        bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
g = mesh_obj('Boden', bm, ground_m)
for p in g.data.polygons:
    p.use_smooth = True


# ---------- Tor in der Felswand ----------
# Tor steht bei y = 0, Öffnung zeigt nach -y (zur Kamera). Plattform 1,6 m hoch, Treppe davor.

GATE_W, GATE_SPRING = 3.6, 5.0
PLAT = 1.6
pts, apex = arch_profile(GATE_W, GATE_SPRING)

# Wandblock mit ausgeschnittener Öffnung
crown = [(x, 10.5 + 2.5 * noise.noise(Vector((x * 0.4, 0.5, 0.5))) + random.uniform(-0.4, 0.4)) for x in [9 - i * 0.75 for i in range(25)]]
wall = prism('Torwand', [(-9, 0), (9, 0)] + crown, -1.2, 1.2, wall_m)
wall.location.z = PLAT
cut = prism('Ausschnitt', pts, -3, 3)
cut.location.z = PLAT
mod = wall.modifiers.new('Loch', 'BOOLEAN')
mod.object = cut
mod.operation = 'DIFFERENCE'
cut.hide_render = True
cut.hide_viewport = True

# Rahmen: zweite, etwas größere Bogenlaibung, die vorsteht
frame_pts, _ = arch_profile(GATE_W + 1.2, GATE_SPRING + 0.2)
frame = prism('Rahmen', frame_pts, -1.6, -1.15, stone)
# Strebepfeiler mit Spitzdach links und rechts des Tores
for sx in (-1, 1):
    tw = prism('Pfeiler', [(-0.8, 0), (0.8, 0), (0.8, 11.5), (0, 13.2), (-0.8, 11.5)], -2.4, 0.5, wall_m)
    tw.location = (sx * (GATE_W / 2 + 1.6), 0, PLAT)
frame.location.z = PLAT - 0.01
fcut = prism('Rahmenloch', pts, -3, 3)
fcut.location.z = PLAT
m2 = frame.modifiers.new('Loch', 'BOOLEAN')
m2.object = fcut
m2.operation = 'DIFFERENCE'
fcut.hide_render = True
fcut.hide_viewport = True

# Torflügel: Profil halbiert, Angeln an den Seiten
def half(sign):
    hp = [(x, z) for x, z in pts if x * sign >= -1e-6]
    hp = sorted(set(hp), key=lambda p: math.atan2(p[1] - 2.5, p[0] * sign))
    hp = [(0, 0)] + [p for p in hp if p != (0, 0)] + [(0, apex)]
    # Punkte relativ zur Angel verschieben
    hx = sign * GATE_W / 2
    hp = [(x * 0.985 - hx, z) for x, z in hp]
    o = prism('Fluegel', hp, -0.15, 0.15, door_m)
    o.location = (hx, 0.4, PLAT)
    return o

door_l, door_r = half(-1), half(1)

# Licht hinter dem Tor
portal = prism('Torlicht', pts, 1.4, 1.45, portal_m)
portal.location.z = PLAT
gate_spot = bpy.data.lights.new('Torstrahl', 'SPOT')
gate_spot.color = GOLD
gate_spot.spot_size = math.radians(70)
gate_spot.spot_blend = 0.6
gate_spot.shadow_soft_size = 0.8
gs = link(bpy.data.objects.new('Torstrahl', gate_spot))
gs.location = (0, 3.5, PLAT + 3.2)
gs.rotation_euler = (math.radians(95), 0, 0)  # schaut nach -y, leicht nach unten

# Plattform und Treppe
plat = prism('Plattform', [(-9, 0), (9, 0), (9, PLAT), (-9, PLAT)], -4, 1.3, stone)
for i in range(8):
    h = PLAT * (i + 1) / 8
    st = prism(f'Stufe{i}', [(-3.2, 0), (3.2, 0), (3.2, h), (-3.2, h)],
               -4 - (8 - i) * 0.5, -4 - (7 - i) * 0.5, stone)

# Felsmassen links und rechts der Torwand, Brocken davor
for k, (x, y, s) in enumerate([(-14, 2, 9), (15, 3, 10), (-24, 8, 14), (26, 10, 15), (-11, -6, 3), (12, -7, 3.5),
                                (-7.5, -12, 1.4), (8, -16, 1.8), (-9, -25, 2.5), (10, -33, 3)]):
    rock(f'Fels{k}', (x, y, s * 0.35), (s, s * 0.8, s * 1.1), rockmat, k)

# Ferne Berge
for k in range(14):
    x = (k - 6.5) * 32 + random.uniform(-8, 8)
    s = random.uniform(25, 55)
    rock(f'Berg{k}', (x, random.uniform(110, 160), -s * 0.2), (s, s * 0.5, s * 1.3), rockmat, 50 + k, 0.6)


# ---------- Ruinensäulen am Weg ----------

def column(name, x, y, h, broken, tilt):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.55, radius2=0.5, depth=h)
    # Kanneluren und Bruchkante
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        rr = 1 + 0.04 * math.cos(a * 16)
        v.co.x *= rr
        v.co.y *= rr
        if broken and v.co.z > h / 2 - 0.01:
            v.co.z += noise.noise(Vector((v.co.x * 3, v.co.y * 3, x))) * 0.6 - 0.3
    o = mesh_obj(name, bm, stone)
    o.location = (x, y, h / 2 + ground_height(x, y) - 0.1)
    o.rotation_euler = (tilt, tilt * 0.5, random.random())
    # Sockel und Kapitell
    for dz, r in ((-h / 2, 0.75), (h / 2, 0.72)):
        if dz > 0 and broken:
            continue
        bmc = bmesh.new()
        bmesh.ops.create_cube(bmc, size=1)
        c = mesh_obj(name + '_platte', bmc, stone)
        c.parent = o
        c.location = (0, 0, dz)
        c.scale = (r * 2, r * 2, 0.35)
    return o

for k, y in enumerate(range(-46, -10, 6)):
    for side in (-1, 1):
        broken = random.random() < 0.55
        h = random.uniform(3, 5) if broken else 6.5
        column(f'Saeule{k}{side}', side * random.uniform(4.6, 5.4), y + random.uniform(-1, 1), h, broken,
               random.uniform(-0.06, 0.06))
# Eine umgestürzte Säule im Vordergrund
fallen = column('Gestuerzt', -3.8, -38, 6, True, 0)
fallen.rotation_euler = (math.radians(86), 0, math.radians(-30))
fallen.location.z = 0.45


# ---------- Wanderer ----------
# Steht vor der Treppe, Blick zum Tor. Umhang flattert über ein bewegtes Rauschfeld.

W = Vector((0.9, -10.5, ground_height(0.9, -10.5)))
wanderer = link(bpy.data.objects.new('Wanderer', None))
wanderer.location = W

bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=0.62, radius2=0.2, depth=1.6)
cloak = mesh_obj('Umhang', bm, cloth)
cloak.parent = wanderer
cloak.location = (0, 0, 0.8)
cloak.scale = (1.0, 0.8, 1)
sub = cloak.modifiers.new('Glatt', 'SUBSURF')
sub.levels = sub.render_levels = 2
# Falten
folds = bpy.data.textures.new('Falten', 'STUCCI')
folds.noise_scale = 0.25
d1 = cloak.modifiers.new('Falten', 'DISPLACE')
d1.texture = folds
d1.strength = 0.06
# Wehen: Rauschfeld folgt einem bewegten Hilfsobjekt
wind = bpy.data.textures.new('Wind', 'CLOUDS')
wind.noise_scale = 0.6
wind_empty = link(bpy.data.objects.new('Wind', None))
d2 = cloak.modifiers.new('Wehen', 'DISPLACE')
d2.texture = wind
d2.texture_coords = 'OBJECT'
d2.texture_coords_object = wind_empty
d2.strength = 0.22
d2.mid_level = 0.5
key(wind_empty, 'location', [(1, (0, 0, 0)), (TOTAL, (7, 2, -3))], 'LINEAR')
for p in cloak.data.polygons:
    p.use_smooth = True

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1)
shoulders = mesh_obj('Schultern', bm, cloth)
shoulders.parent = wanderer
shoulders.location = (0, 0, 1.48)
shoulders.scale = (0.32, 0.2, 0.12)
shoulders.location.z = 1.44

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1)
# Kapuze: hinten spitz zulaufend
for v in bm.verts:
    if v.co.y > 0.2 and v.co.z > -0.2:
        v.co.y += (v.co.y - 0.2) * 0.6 * (v.co.z + 0.2)
hood = mesh_obj('Kapuze', bm, cloth)
hood.parent = wanderer
hood.location = (0, 0.02, 1.72)
hood.scale = (0.15, 0.17, 0.19)
for o in (shoulders, hood):
    for p in o.data.polygons:
        p.use_smooth = True

staff_root = link(bpy.data.objects.new('StabGriff', None))
staff_root.parent = wanderer
staff_root.location = (0.38, -0.05, 1.05)
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.028, radius2=0.022, depth=2.0)
staff = mesh_obj('Stab', bm, wood)
staff.parent = staff_root
staff.location = (0, 0, 0.0)
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.06)
tip = mesh_obj('Kristall', bm, crystal)
tip.parent = staff_root
tip.location = (0, 0, 1.05)
tip.scale = (0.8, 0.8, 1.6)
tip_light = bpy.data.lights.new('Stablicht', 'POINT')
tip_light.color = (0.55, 0.65, 1.0)
tip_light.energy = 30
tip_light.shadow_soft_size = 0.05
tl = link(bpy.data.objects.new('Stablicht', tip_light))
tl.parent = staff_root
tl.location = (0, 0, 1.1)

# Stab: in Einstellung 3 hebt er ihn an, beim Ausbruch hoch erhoben
key(staff_root, 'location', [(196, (0.38, -0.05, 1.05)), (232, (0.38, -0.05, 1.05)), (262, (0.4, -0.15, 1.45)),
                            (390, (0.4, -0.15, 1.45))])
key(staff_root, 'rotation_euler', [(196, (0, 0.05, 0)), (232, (0, 0.05, 0)), (262, (math.radians(-12), 0.1, 0))])


# ---------- Torhandlung: Runen glühen, Tor reißt auf, Licht flutet ----------

def anim_value(socket_owner, attr, frames_values, data_path=None):
    for f, v in frames_values:
        setattr(socket_owner, attr, v)
        socket_owner.keyframe_insert(attr if data_path is None else data_path, frame=f)

anim_value(RUNE, 'default_value', [(1, 0.6), (210, 0.6), (250, 8), (285, 14), (300, 40), (330, 5)])
anim_value(gate_spot, 'energy', [(1, 6000), (240, 6000), (285, 15000), (292, 15000), (305, 50000), (390, 40000)])
anim_value(portal_m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'], 'default_value',
           [(1, 4), (285, 12), (292, 12), (308, 120), (390, 100)])
OPEN = math.radians(78)
for door, sign in ((door_l, -1), (door_r, 1)):
    key(door, 'rotation_euler', [(1, (0, 0, 0)), (293, (0, 0, 0)), (322, (0, 0, -sign * OPEN)),
                                (390, (0, 0, -sign * OPEN * 1.03))])
    # kurzes Rucken vor dem Aufreißen
    key(door, 'location', [(286, door.location.copy()), (290, door.location + Vector((0, -0.04, 0))),
                           (293, door.location.copy())])


# ---------- Funken ----------
# Glut steigt ständig vom Boden am Tor auf; beim Ausbruch schießt ein Schwarm nach vorn.

bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.025)
spark_mesh = bpy.data.meshes.new('Funke')
bm.to_mesh(spark_mesh)
bm.free()
spark_mesh.materials.append(spark_m)

def spark(name, path_fn, f0, f1, step=3):
    o = link(bpy.data.objects.new(name, spark_mesh))
    o.scale = (0, 0, 0)
    o.keyframe_insert('scale', frame=max(1, f0 - 1))
    for f in range(f0, f1 + 1, step):
        o.location = path_fn(f)
        o.keyframe_insert('location', frame=f)
    s = random.uniform(0.6, 1.6)
    o.scale = (s, s, s)
    o.keyframe_insert('scale', frame=f0)
    o.keyframe_insert('scale', frame=f1 - 1)
    o.scale = (0, 0, 0)
    o.keyframe_insert('scale', frame=f1)

for k in range(140):
    # aufsteigende Glut
    x0, y0 = random.uniform(-7, 7), random.uniform(-30, -1)
    f0 = random.randint(1 - 120, TOTAL - 20)
    life = random.randint(90, 160)
    vz, ph = random.uniform(0.6, 1.2), random.uniform(0, 6)
    def p(f, x0=x0, y0=y0, f0=f0, vz=vz, ph=ph):
        t = (f - f0) / FPS
        return (x0 + 0.4 * math.sin(t * 1.7 + ph) + t * 0.5, y0 + 0.3 * math.cos(t * 1.3 + ph),
                ground_height(x0, y0) + 0.2 + t * vz)
    spark(f'Glut{k}', p, max(1, f0), min(TOTAL, f0 + life))

for k in range(160):
    # Ausbruch aus dem Tor in Richtung Kamera
    a = random.uniform(0, 2 * math.pi)
    spread = random.uniform(0.1, 1.0)
    v = Vector((math.cos(a) * spread * 6, -random.uniform(8, 22), math.sin(a) * spread * 4 + 3))
    f0 = random.randint(300, 340)
    def p(f, v=v, f0=f0):
        t = (f - f0) / FPS
        return (v.x * t, 0.5 + v.y * t, PLAT + 2.2 + v.z * t - 4.0 * t * t)
    life = min(random.randint(25, 60), int(11 / -v.y * FPS))  # höchstens 11 m nach vorn
    spark(f'Funke{k}', p, f0, min(TOTAL, f0 + life), step=1)


# ---------- Licht, Himmel, Nebel ----------

moon = bpy.data.lights.new('Mond', 'SUN')
moon.color = BLUE
moon.energy = 0.9
moon.angle = math.radians(3)
mo = link(bpy.data.objects.new('Mond', moon))
mo.rotation_euler = (math.radians(55), math.radians(25), math.radians(-160))

# Gegenlicht von hinten oben (zeichnet Kanten nach)
rim = bpy.data.lights.new('Kante', 'SUN')
rim.color = (0.6, 0.45, 1.0)
rim.energy = 1.4
ro = link(bpy.data.objects.new('Kante', rim))
ro.rotation_euler = (math.radians(70), 0, math.radians(10))

world = bpy.data.worlds.new('Himmel')
scene.world = world
wn = world.node_tree.nodes
wl = world.node_tree.links
bg = wn['Background']
geo = wn.new('ShaderNodeTexCoord')
sep = wn.new('ShaderNodeSeparateXYZ')
wl.new(geo.outputs['Generated'], sep.inputs[0])
sky = wn.new('ShaderNodeValToRGB')
sky.color_ramp.elements[0].position = 0.0
sky.color_ramp.elements[0].color = (0.09, 0.06, 0.16, 1)   # Horizont violett
sky.color_ramp.elements[1].position = 0.45
sky.color_ramp.elements[1].color = (0.006, 0.008, 0.025, 1)  # oben fast schwarzblau
wl.new(sep.outputs['Z'], sky.inputs['Fac'])
# Wolkenbänder
cl = wn.new('ShaderNodeTexNoise')
cl.inputs['Scale'].default_value = 3.0
cl.inputs['Detail'].default_value = 10
cl.inputs['Roughness'].default_value = 0.65
cramp = wn.new('ShaderNodeValToRGB')
cramp.color_ramp.elements[0].position = 0.45
cramp.color_ramp.elements[1].position = 0.75
cramp.color_ramp.elements[1].color = (0.11, 0.09, 0.2, 1)
cramp.color_ramp.elements[0].color = (0, 0, 0, 1)
wl.new(geo.outputs['Generated'], cl.inputs['Vector'])
wl.new(cl.outputs['Fac'], cramp.inputs['Fac'])
add = wn.new('ShaderNodeMix')
add.data_type = 'RGBA'
add.blend_type = 'ADD'
add.inputs['Factor'].default_value = 1
wl.new(sky.outputs['Color'], add.inputs['A'])
wl.new(cramp.outputs['Color'], add.inputs['B'])
# Sterne
st = wn.new('ShaderNodeTexVoronoi')
st.inputs['Scale'].default_value = 400
sramp = wn.new('ShaderNodeValToRGB')
sramp.color_ramp.elements[0].position = 0.0
sramp.color_ramp.elements[0].color = (1.2, 1.2, 1.5, 1)
sramp.color_ramp.elements[1].position = 0.04
sramp.color_ramp.elements[1].color = (0, 0, 0, 1)
wl.new(geo.outputs['Generated'], st.inputs['Vector'])
wl.new(st.outputs['Distance'], sramp.inputs['Fac'])
add2 = wn.new('ShaderNodeMix')
add2.data_type = 'RGBA'
add2.blend_type = 'ADD'
add2.inputs['Factor'].default_value = 1
wl.new(add.outputs['Result'], add2.inputs['A'])
wl.new(sramp.outputs['Color'], add2.inputs['B'])
wl.new(add2.outputs['Result'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0

# Nebel: dünner Dunst überall, dichter Bodennebel, der durch die Szene zieht
def fog_box(name, loc, dims, density, ground=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    vol = nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.75, 0.75, 0.9, 1)
    vol.inputs['Anisotropy'].default_value = 0.35  # streut nach vorn: Lichtstrahlen
    out = nt.nodes['Material Output']
    if ground:
        tc = nt.nodes.new('ShaderNodeNewGeometry')
        mp = nt.nodes.new('ShaderNodeMapping')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 0.12
        nz.inputs['Detail'].default_value = 4
        sep2 = nt.nodes.new('ShaderNodeSeparateXYZ')
        fall = nt.nodes.new('ShaderNodeMapRange')  # unten dicht, nach oben ausdünnen
        fall.inputs['From Min'].default_value = 0.0
        fall.inputs['From Max'].default_value = 2.2
        fall.inputs['To Min'].default_value = 1.0
        fall.inputs['To Max'].default_value = 0.0
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        shape = nt.nodes.new('ShaderNodeMapRange')
        shape.inputs['From Min'].default_value = 0.4
        shape.inputs['From Max'].default_value = 0.7
        shape.inputs['To Max'].default_value = density
        nt.links.new(tc.outputs['Position'], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], shape.inputs['Value'])
        nt.links.new(tc.outputs['Position'], sep2.inputs[0])
        nt.links.new(sep2.outputs['Z'], fall.inputs['Value'])
        nt.links.new(shape.outputs['Result'], mul.inputs[0])
        nt.links.new(fall.outputs['Result'], mul.inputs[1])
        nt.links.new(mul.outputs[0], vol.inputs['Density'])
        mp.inputs['Location'].default_value = (0, 0, 0)
        mp.inputs['Location'].keyframe_insert('default_value', frame=1)
        mp.inputs['Location'].default_value = (14, 6, 0)
        mp.inputs['Location'].keyframe_insert('default_value', frame=TOTAL)
        for fc in action_fcurves(nt):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    else:
        vol.inputs['Density'].default_value = density
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    o = mesh_obj(name, bm, m)
    o.location = loc
    o.scale = dims
    return o

fog_box('Dunst', (0, 20, 15), (160, 200, 40), 0.004)
fog_box('Bodennebel', (0, -15, 1.5), (60, 70, 5), 0.08, ground=True)


# ---------- Kameras ----------
# Jede Einstellung hat eine eigene Kamera und ein Ziel; Schnitte über Zeitmarken.
# Querformat: Blickpunkt rechts (Kamera schaut links daran vorbei). Hochformat: Blickpunkt oben.

def camera(name, lens, path, target_path, f0, f1, fstop=None, focus=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens if not PORTRAIT else lens * 0.62
    cd.sensor_width = 36
    cd.clip_end = 1000
    cam = link(bpy.data.objects.new(name, cd))
    tgt = link(bpy.data.objects.new(name + '_Ziel', None))
    c = cam.constraints.new('TRACK_TO')
    c.target = tgt
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    key(cam, 'location', path)
    key(tgt, 'location', target_path)
    # Querformat: Motiv nach rechts; Hochformat: Motiv nach oben
    if PORTRAIT:
        cd.shift_y = -0.12
    else:
        cd.shift_x = -0.17
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        for f, d in focus:
            cd.dof.focus_distance = d
            cd.dof.keyframe_insert('focus_distance', frame=f)
    m = scene.timeline_markers.new(name, frame=f0)
    m.camera = cam
    return cam, tgt

def shake(obj, f0, f1, amount, scale=4):
    """Kamerawackeln: Rauschen auf der Position des Ziels, nur im Bereich f0..f1."""
    for fc in action_fcurves(obj):
        if fc.data_path != 'location':
            continue
        m = fc.modifiers.new('NOISE')
        m.scale = scale
        m.strength = amount
        m.phase = fc.array_index * 17 + f0
        m.use_restricted_range = True
        m.frame_start, m.frame_end = f0, f1
        m.blend_in = m.blend_out = 3

a, b = SHOTS['totale']
cam1, t1 = camera('1_Totale', 32, [(a, (-3.5, -78, 2.0)), (b, (-2.5, -71, 5.0))],
                  [(a, (0, 0, 5.5)), (b, (0, 0, 5.0))], a, b, 4.0, [(a, 75)])

a, b = SHOTS['fahrt']
cam2, t2 = camera('2_Fahrt', 22, [(a, (-1.5, -52, 1.6)), (a + 60, (0.2, -27, 2.4)), (b, (0.6, -17.5, 2.8))],
                  [(a, (0, 0, 4)), (b, (0, 0, 4.6))], a, b, 2.8, [(a, 50), (b, 18)])
cam2.rotation_mode = 'XYZ'
shake(t2, a, b, 0.25, 6)

a, b = SHOTS['nah']
# Über die Schulter: Wanderer unscharf im Vordergrund, Schärfe auf den Runen
cam3, t3 = camera('3_Nah', 45, [(a, (1.95, -12.5, 1.5)), (b, (1.8, -12.15, 1.6))],
                  [(a, (-1.2, 0, 3.0)), (b, (-1.2, 0, 3.3))], a, b, 1.0,
                  [(a, 13.2), (b, 12.7)])

a, b = SHOTS['ausbruch']
cam4, t4 = camera('4_Ausbruch', 30, [(a, (1.45, -13.4, 0.9)), (300, (1.45, -13.5, 0.9)), (b, (1.4, -14.6, 1.0))],
                  [(a, (-0.6, 0, 3.8)), (b, (-0.6, 0, 4.1))], a, b, 2.8, [(a, 3.0), (b, 4.1)])
shake(t4, 300, b, 0.35, 3)
scene.camera = cam1


# ---------- Rendern ----------

r = scene.render
r.engine = 'BLENDER_EEVEE'
r.resolution_x, r.resolution_y = (1080, 1920) if PORTRAIT else (1920, 1080)
r.resolution_percentage = args.pct
r.use_motion_blur = True
r.motion_blur_shutter = 0.5
r.image_settings.file_format = 'PNG'
ee = scene.eevee
ee.taa_render_samples = args.samples
ee.volumetric_tile_size = '4'
ee.volumetric_samples = 96
ee.volumetric_end = 260
ee.use_volumetric_shadows = True
ee.volumetric_shadow_samples = 32
ee.volumetric_light_clamp = 0
ee.use_raytracing = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Punchy'
scene.view_settings.exposure = 0.3

# Leuchten (Bloom) über den Compositor
comp = bpy.data.node_groups.new('Nachbearbeitung', 'CompositorNodeTree')
scene.compositing_node_group = comp
comp.interface.new_socket('Bild', in_out='OUTPUT', socket_type='NodeSocketColor')
rl = comp.nodes.new('CompositorNodeRLayers')
gl = comp.nodes.new('CompositorNodeGlare')
out = comp.nodes.new('NodeGroupOutput')
for name, val in (('Type', 'Bloom'), ('Quality', 'High')):
    if name in gl.inputs:
        gl.inputs[name].default_value = val
if 'Threshold' in gl.inputs:
    gl.inputs['Threshold'].default_value = 0.8
if 'Strength' in gl.inputs:
    gl.inputs['Strength'].default_value = 0.45
if 'Size' in gl.inputs:
    gl.inputs['Size'].default_value = 0.6
comp.links.new(rl.outputs['Image'], gl.inputs['Image'])
comp.links.new(gl.outputs['Image'], out.inputs[0])

if args.save:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('blender/szene.blend'))

frames = []
for part in args.frames.split(','):
    if '-' in part:
        s, e = part.split('-')
        frames += range(int(s), int(e) + 1)
    else:
        frames.append(int(part))

os.makedirs(args.out, exist_ok=True)
import time
for f in frames:
    path = os.path.abspath(os.path.join(args.out, f'{f:04d}.png'))
    if os.path.exists(path):
        continue
    t0 = time.time()
    scene.frame_set(f)
    r.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f'BILD {f} fertig in {time.time() - t0:.1f} s', flush=True)

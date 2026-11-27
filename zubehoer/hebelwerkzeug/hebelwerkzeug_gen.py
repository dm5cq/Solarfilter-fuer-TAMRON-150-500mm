#!/usr/bin/env python3
"""
Hebelwerkzeug zum Abloesen der Filtereinheit vom Traeger (Solarfilter Tamron 150-500)
Autor: Stefan J. Kaiser DM5CQ / OE8KKS
Lizenz: CC BY-NC-SA 4.0 (siehe LICENSE.md)

Griff Ø20 x 50 mm (hinten halbkugelig gerundet, Ø5-Bohrung fuer Lanyard),
Spachtel 18 x 23 x 1,5 mm mit gerundeten Vorderecken.
Spachtel mittig auf der Griffachse, beidseitiger Anschliff.
Drucklage: liegend, Spachtel waagrecht in Griffmitte (mit Stuetzstruktur drucken).
Magnet 10 x 3 mm flach in der Spachtelebene, Griffmitte: Hohlraum z = 8,4 ... 11,6 mm
-> Druckpause bei 11,6 mm, Magnet einlegen.

Aufruf: python3 hebelwerkzeug_gen.py [ausgabe.stl]   (numpy, scikit-image)
Erzeugt zusaetzlich eine .3mf mit eingebetteten Druckeinstellungen (100 % Infill, 6 Waende,
Stuetzen nur vom Bett) und Druckpause fuer den Magneten (Bambu Studio / Orca Slicer / PrusaSlicer).
"""
import sys, os, struct
import numpy as np
from skimage.measure import marching_cubes

# ------------------------------------------------------------------ Parameter
GRIFF_D      = 20.0   # Griffdurchmesser
GRIFF_L      = 50.0   # Grifflaenge inkl. Rundung
LANYARD_D    = 5.0    # Bohrung fuer Lanyard
LANYARD_ABST = 7.0    # Mitte Bohrung vom Griffende
SPATEL_B     = 18.0
SPATEL_L     = 23.0   # freie Laenge vor dem Griff
SPATEL_T     = 1.5
ECK_R        = 4.0    # Rundung der vorderen Ecken
FASE_L       = 4.0    # Anschliff vorne (oben), 0 = kein Anschliff
FASE_T       = 0.6    # Dicke an der Spitze (beidseitig angeschliffen)
KANTE_R      = 1.5    # Rundung der vorderen Griffkante
UEBERGANG_R  = 3.0    # Ausrundung Spachtel -> Griff
MAGNET_D     = 10.0   # eingedruckter Neodym-Magnet (Druckpause!)
MAGNET_H     = 3.0
MAGNET_SPIEL = 0.2    # Zugabe auf Durchmesser und Hoehe
MAGNET_POS   = 25.0   # Mitte Hohlraum ab Griffende (= Griffmitte)
VOXEL        = 0.2    # Aufloesung (feiner als die 0,2-mm-Druckschichten noetig waere bringt nichts)

R = GRIFF_D/2
XK = GRIFF_L - R                            # Zentrum der Endrundung

def smin(a, b, k):
    h = np.clip(0.5 + 0.5*(b-a)/k, 0, 1)
    return b*(1-h) + a*h - k*h*(1-h)
def smax(a, b, k):
    return -smin(-a, -b, k)

def sdf(x, y, z):
    """lokale Koordinaten: x = Werkzeugachse (Spitze bei -SPATEL_L, Griffende bei GRIFF_L),
    Spachtel in der x/y-Ebene, Dicke in z, alles mittig auf der Achse."""
    ryz = np.sqrt(y**2 + z**2)
    # Griff: Zylinder mit gerundeter Vorderkante + Halbkugel hinten
    rr = KANTE_R
    qx = -x + rr; qr = ryz - (R - rr)
    front = np.where((qx > 0) & (qr > 0), np.sqrt(qx**2 + qr**2) - rr, np.maximum(-x, ryz - R))
    sph = np.sqrt((x-XK)**2 + y**2 + z**2) - R
    griff = np.where(x > XK, sph, front)
    # Spachtel
    x0, x1 = -SPATEL_L, 6.0
    cx, hx, hy = (x0+x1)/2, (x1-x0)/2, SPATEL_B/2
    qx = np.abs(x-cx) - (hx-ECK_R); qy = np.abs(y) - (hy-ECK_R)
    d2 = np.sqrt(np.maximum(qx, 0)**2 + np.maximum(qy, 0)**2) + np.minimum(np.maximum(qx, qy), 0) - ECK_R
    dick = np.full_like(x, SPATEL_T)
    if FASE_L > 0:
        t = np.clip((x - x0)/FASE_L, 0, 1)
        dick = FASE_T + (SPATEL_T-FASE_T)*t
    spatel = np.maximum(d2, np.abs(z) - dick/2)
    d = smin(griff, spatel, UEBERGANG_R)
    loch = np.sqrt((x-(GRIFF_L-LANYARD_ABST))**2 + y**2) - LANYARD_D/2   # quer zur Spachtelebene
    d = smax(d, -loch, 0.6)
    # geschlossener Hohlraum fuer den Magneten, flach in der Spachtelebene (liegt beim liegenden Druck waagrecht)
    xm = GRIFF_L - MAGNET_POS; hh = (MAGNET_H + MAGNET_SPIEL)/2
    mag = np.maximum(np.sqrt((x - xm)**2 + y**2) - (MAGNET_D + MAGNET_SPIEL)/2, np.abs(z) - hh)
    d = np.maximum(d, -mag)
    return d

def build():
    v = VOXEL
    xs = np.arange(-SPATEL_L-1.0+0.013, GRIFF_L+1.0+v, v)
    ys = np.arange(-SPATEL_B/2-1.5+0.017, SPATEL_B/2+1.5+v, v)
    zs = np.arange(-R-1.0+0.011, R+1.0+v, v)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
    F = sdf(X, Y, Z).astype(np.float32)
    F[0], F[-1], F[:, 0], F[:, -1], F[:, :, 0], F[:, :, -1] = 1, 1, 1, 1, 1, 1
    verts, faces, _, _ = marching_cubes(F, 0.0, spacing=(v, v, v))
    verts += np.array([xs[0], ys[0], zs[0]])
    # fast deckungsgleiche Punkte verschweissen, entartete Dreiecke entfernen
    q = np.round(verts / 2e-3).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    verts = q[first] * 2e-3; faces = inv.reshape(-1)[faces]
    ok = (faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])
    faces = faces[ok]
    # doppelte Gegen-Dreieckspaare (nach dem Verschweissen) entfernen
    key = np.sort(faces, axis=1)
    _, idx, cnt = np.unique(key, axis=0, return_index=True, return_counts=True)
    faces = faces[np.isin(np.arange(len(faces)), idx[cnt == 1])]
    t = verts[faces]
    vol = np.sum(np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2]))) / 6
    if vol < 0:
        t = t[:, [0, 2, 1]]; vol = -vol
    # liegend: Griffachse waagrecht, Spachtel in halber Griffhoehe
    t[:, :, 2] -= t[:, :, 2].min()
    return t, vol

def save_stl(path, t, name):
    n = np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]); l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1
    rec = np.zeros(len(t), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    rec['n'] = n/l; rec['v'] = t
    with open(path, 'wb') as f:
        f.write(name.encode()[:80].ljust(80, b' ')); f.write(struct.pack('<I', len(t))); f.write(rec.tobytes())

# ---------------------------------------------------------- 3MF mit Druckeinstellungen
DRUCK = {   # fuer maximale Hebelkraefte: voll massiv, viele Wandlinien
    'infill': 100, 'waende': 6, 'boden_deckel': 8, 'schicht': 0.2,
}
def save_3mf(path, t, name):
    """3MF mit eingebetteten Objekt-Einstellungen (Bambu Studio / Orca Slicer und PrusaSlicer)
    + Druckpause zum Einlegen des Magneten."""
    import zipfile
    q = np.round(t.reshape(-1, 3).astype(np.float32), 4)
    uv, inv = np.unique(q, axis=0, return_inverse=True)
    tri = inv.reshape(-1, 3)
    vs = "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in uv)
    ts = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
    model = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="de-DE" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<metadata name="Title">{name}</metadata>
<metadata name="Designer">Stefan J. Kaiser DM5CQ / OE8KKS</metadata>
<metadata name="License">CC BY-NC-SA 4.0</metadata>
<resources><object id="1" type="model"><mesh><vertices>
{vs}
</vertices><triangles>
{ts}
</triangles></mesh></object></resources>
<build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 120 120 0"/></build>
</model>"""
    D = DRUCK
    pause_z = round(R + (MAGNET_H + MAGNET_SPIEL)/2 + D['schicht'], 2)   # erste Schicht ueber dem Hohlraum
    bambu = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="1">
    <metadata key="name" value="{name}"/>
    <metadata key="extruder" value="1"/>
    <metadata key="sparse_infill_density" value="{D['infill']}%"/>
    <metadata key="sparse_infill_pattern" value="zig-zag"/>
    <metadata key="wall_loops" value="{D['waende']}"/>
    <metadata key="top_shell_layers" value="{D['boden_deckel']}"/>
    <metadata key="bottom_shell_layers" value="{D['boden_deckel']}"/>
    <metadata key="layer_height" value="{D['schicht']}"/>
    <metadata key="enable_support" value="1"/>
    <metadata key="support_on_build_plate_only" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{name}"/>
    </part>
  </object>
</config>"""
    bambu_pause = f"""<?xml version="1.0" encoding="utf-8"?>
<custom_gcodes_per_layer>
<plate>
<plate_info id="1"/>
<layer top_z="{pause_z}" type="1" extruder="1" color="" extra="Magnet 10x3 einlegen" gcode="M400 U1"/>
<mode value="SingleExtruder"/>
</plate>
</custom_gcodes_per_layer>"""
    prusa = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
 <object id="1" instances_count="1">
  <metadata type="object" key="name" value="{name}"/>
  <metadata type="object" key="fill_density" value="{D['infill']}%"/>
  <metadata type="object" key="fill_pattern" value="rectilinear"/>
  <metadata type="object" key="perimeters" value="{D['waende']}"/>
  <metadata type="object" key="top_solid_layers" value="{D['boden_deckel']}"/>
  <metadata type="object" key="bottom_solid_layers" value="{D['boden_deckel']}"/>
  <metadata type="object" key="layer_height" value="{D['schicht']}"/>
  <metadata type="object" key="support_material" value="1"/>
  <metadata type="object" key="support_material_buildplate_only" value="1"/>
  <volume firstid="0" lastid="{len(tri)-1}">
   <metadata type="volume" key="name" value="{name}"/>
   <metadata type="volume" key="volume_type" value="ModelPart"/>
  </volume>
 </object>
</config>"""
    prusa_pause = f"""<?xml version="1.0" encoding="utf-8"?>
<custom_gcodes_per_print_z>
<code print_z="{pause_z}" type="1" extruder="1" color="" extra="Magnet 10x3 einlegen" gcode="M601"/>
<mode value="SingleExtruder"/>
</custom_gcodes_per_print_z>"""
    ct = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
<Default Extension="config" ContentType="text/xml"/>
<Default Extension="xml" ContentType="text/xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model)
        z.writestr('Metadata/model_settings.config', bambu)
        z.writestr('Metadata/custom_gcode_per_layer.xml', bambu_pause)
        z.writestr('Metadata/Slic3r_PE_model.config', prusa)
        z.writestr('Metadata/Prusa_Slicer_custom_gcode_per_print_z.xml', prusa_pause)
    return pause_z

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'solarfilter_hebelwerkzeug.stl'
    t, vol = build()
    save_stl(out, t, 'solarfilter_hebelwerkzeug')
    pz = save_3mf(os.path.splitext(out)[0] + '.3mf', t, 'solarfilter_hebelwerkzeug')
    print(f"3MF mit Einstellungen: Infill {DRUCK['infill']} %, {DRUCK['waende']} Waende, Pause bei {pz} mm")
    mn, mx = t.reshape(-1, 3).min(0), t.reshape(-1, 3).max(0)
    hh = (MAGNET_H + MAGNET_SPIEL)/2
    print(f"Magnet-Hohlraum: z = {R-hh:.1f} ... {R+hh:.1f} mm -> Druckpause bei {R+hh:.1f} mm")
    print(f"{out}: {len(t)} Dreiecke, Volumen {vol/1000:.1f} cm3, Masse {mx[0]-mn[0]:.1f} x {mx[1]-mn[1]:.1f} x {mx[2]-mn[2]:.1f}")

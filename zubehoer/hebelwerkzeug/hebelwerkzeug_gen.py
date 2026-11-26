#!/usr/bin/env python3
"""
Hebelwerkzeug zum Abloesen der Filtereinheit vom Traeger (Solarfilter Tamron 150-500)
Autor: Stefan J. Kaiser DM5CQ / OE8KKS
Lizenz: CC BY-NC-SA 4.0 (siehe LICENSE.md)

Griff Ø20 x 50 mm (hinten halbkugelig gerundet, Ø5-Bohrung fuer Lanyard),
Spachtel 18 x 23 x 1,5 mm mit gerundeten Vorderecken.
Spachtel mittig auf der Griffachse, beidseitiger Anschliff.
Drucklage: stehend, gerundetes Griffende unten (mit Stuetzstruktur drucken), Spachtel oben.

Aufruf: python3 hebelwerkzeug_gen.py [ausgabe.stl]   (numpy, scikit-image)
"""
import sys, struct
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
    # stehend: Griffende unten (z=0), Spachtelspitze oben
    t = np.stack([t[:, :, 2], t[:, :, 1], GRIFF_L - t[:, :, 0]], axis=-1)
    t[:, :, 2] -= t[:, :, 2].min()
    return t, vol

def save_stl(path, t, name):
    n = np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]); l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1
    rec = np.zeros(len(t), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    rec['n'] = n/l; rec['v'] = t
    with open(path, 'wb') as f:
        f.write(name.encode()[:80].ljust(80, b' ')); f.write(struct.pack('<I', len(t))); f.write(rec.tobytes())

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'solarfilter_hebelwerkzeug.stl'
    t, vol = build()
    save_stl(out, t, 'solarfilter_hebelwerkzeug')
    mn, mx = t.reshape(-1, 3).min(0), t.reshape(-1, 3).max(0)
    print(f"{out}: {len(t)} Dreiecke, Volumen {vol/1000:.1f} cm3, Masse {mx[0]-mn[0]:.1f} x {mx[1]-mn[1]:.1f} x {mx[2]-mn[2]:.1f}")

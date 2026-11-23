#!/usr/bin/env python3
"""
Solarfilter-Halter fuer Tamron 150-500mm F5-6.7 Di III VC VXD (A057) mit Gegenlichtblende HA057
Plexi (2 mm) + Solarfolie + Plexi (2 mm), Plattenformat 200 x 200 mm.
Autor: Stefan J. Kaiser DM5CQ / OE8KKS
Lizenz: CC BY-NC-SA 4.0 (siehe LICENSE.md)

Erzeugt (alle Masse in mm):
  solarfilter_frontrahmen.stl  - Sonnenseite, Tasche fuer den Plexi-Folie-Plexi-Stapel
  solarfilter_rueckrahmen.stl  - hinterer Deckel, mit Frontrahmen verschraubt (8x M3x15 + Mutter),
                                 8 Magnettaschen + Zentrierring -> Filterpaket haftet magnetisch am Traeger
  solarfilter_traeger.stl      - bleibt auf der GLB: Flansch mit 8 Magnettaschen, 8 U-Taschen fuer
                                 Muttern/Schraubenenden + geschlitztes Rohr
  solarfilter_schutz_frontdeckel.stl / _rueckdeckel.stl - Transportschutz fuer das Filterpaket
  solarfilter_passring.stl     - kurzer Testring mit gleichem Innen-D wie das Rohr (Passprobe)

Benoetigt nur numpy, scipy, matplotlib.  Aufruf: python3 solarfilter_gen.py [Ausgabeordner]
"""
import sys, os, struct
import numpy as np
from scipy.spatial import Delaunay
from matplotlib.path import Path

# ----------------------------------------------------------------- Parameter
GLB_D        = 113.05  # gemessen am Gummiring vorne (Stefan, 21.11.2026)
SPIEL_D      = 1.0     # Durchmesser-Zugabe (0,5 mm radial; Filz 0,5 mm oder Klettband gleicht aus)
ROHR_WAND    = 3.5     # Wandstaerke Rohr
ROHR_LAENGE  = 30.0    # Steckhoehe ueber der GLB
SCHLITZE     = 8       # Anzahl Federzungen
SCHLITZ_B    = 2.5     # Schlitzbreite
SCHLITZ_START= 6.0     # Schlitze beginnen x mm oberhalb Flansch
NUT_TIEFE    = 1.0     # Riemen-/Schellennut aussen
NUT_Z        = (7.0, 21.0)   # Nut von/bis (ab Flanschoberseite)
FASE         = 0.75    # Einfuehrstufe innen am Rohrende (radial)
LIPPE        = 2.5     # Anschlag-Lippe radial nach innen (GLB-Kante liegt hier an)

PLATTE       = 200.0   # Plexi-Kantenlaenge
PLATTE_SPIEL = 1.0     # Gesamtspiel in der Tasche (Waermeausdehnung PMMA!)
STAPEL       = 5.0     # Dicke Plexi + Folie + Plexi (gemessen)
AUSSEN       = 216.0   # Aussenmass Rahmen/Flansch
ECK_R        = 4.0     # Aussen-Eckradius
FRONT_LIPPE  = 2.5     # Dicke der vorderen Lippe (Sonnenseite)
FENSTER      = 186.0   # sichtbares Fenster vorne
FENSTER_R    = 6.0
FLANSCH      = 5.0     # Flanschdicke Traeger (Boden ueber den Mutter-Taschen 1,6 mm)
SCHRAUBE_D   = 3.4     # M3-Durchgang
SCHR_POS     = 104.5   # Abstand Schraubenreihe von Mitte
SCHR_OFF     = 50.0    # Versatz entlang der Kante (8 Schrauben)
PASSRING_H   = 8.0
# --- Schnellwechsel per Neodym-Magnet (Traeger bleibt auf der GLB)
MAG_D        = 10.0    # Magnet-Durchmesser
MAG_H        = 3.0     # Magnet-Hoehe (ANNAHME 10x3 mm -> anpassen!)
MAG_SPIEL    = 0.2     # Tasche = MAG_D + Spiel (Magnete einkleben)
MAG_POS      = 100.5   # Magnetreihe: 4 Ecken + 4 Kantenmitten
RUECK_DICKE  = 4.5     # Rueckrahmen (haelt den Plattenstapel, traegt Magnete + Einschmelzmuttern)
SCHR_LAENGE  = 15.0    # M3x15: Frontrahmen + Rueckrahmen + Mutter
MUTTER_SW    = 5.5     # M3-Mutter Schluesselweite (DIN 934), Hoehe 2,4
MUTTER_TASCHE_B = 7.2  # Breite der U-Tasche im Traegerflansch (Mutter frei drehbar, Eckmass 6,35)
ZENTRIER_H   = 2.0     # Zentrierring am Rueckrahmen, greift in die Flanschoeffnung
ZENTRIER_SP  = 0.4     # radiales Spiel Zentrierring

SEG_MM = 0.9           # max. Segmentlaenge auf Boegen

# ------------------------------------------------------------ Geometrie-Kern
class Mesh2p5D:
    """2,5D-Koerper aus gestapelten Lagen. Jede Lage = Menge geschlossener Konturen (gerade/ungerade-Regel).
    Konturen teilen Eckpunkte ueber ein globales Register -> wasserdichtes, mannigfaltiges Netz."""
    def __init__(self):
        self.pts = []; self.key = {}
        self.slabs = []   # (z0, z1, [loop(list of ids)])
    def vid(self, x, y):
        k = (round(x, 5), round(y, 5))
        if k not in self.key:
            self.key[k] = len(self.pts); self.pts.append(k)
        return self.key[k]
    def loop(self, xy):
        ids = [self.vid(x, y) for x, y in xy]
        out = [ids[0]]
        for i in ids[1:]:
            if i != out[-1]: out.append(i)
        if out[0] == out[-1]: out.pop()
        return out
    def slab(self, z0, z1, loops):
        self.slabs.append((z0, z1, loops))

    # -- Hilfen
    def _P(self): return np.array(self.pts, float)
    @staticmethod
    def _edges(loop):
        return [(loop[i], loop[(i+1) % len(loop)]) for i in range(len(loop))]
    def _contains(self, loops, q):
        P = self._P(); c = np.zeros(len(q), int)
        for L in loops:
            c += Path(P[L]).contains_points(q).astype(int)
        return c % 2 == 1
    def _depth_parity(self, loops, idx):
        P = self._P(); L = loops[idx]
        # Testpunkt: Mitte einer Kante leicht versetzt reicht nicht sicher -> Schwerpunkt eines Eckpunkts
        q = P[L[0]][None]
        d = 0
        for j, M in enumerate(loops):
            if j != idx and Path(P[M]).contains_point(q[0]): d += 1
        return d % 2
    def _split_edge(self, a, b):
        P = self._P(); m = (P[a] + P[b]) / 2
        w = self.vid(m[0], m[1])
        for (_, _, loops) in self.slabs:
            for L in loops:
                n = len(L)
                for i in range(n):
                    u, v = L[i], L[(i+1) % n]
                    if (u, v) == (a, b) or (u, v) == (b, a):
                        L.insert(i+1, w); break

    def _levels(self):
        zs = sorted(set([s[0] for s in self.slabs] + [s[1] for s in self.slabs]))
        res = []
        for z in zs:
            A = [s[2] for s in self.slabs if abs(s[1]-z) < 1e-9]
            B = [s[2] for s in self.slabs if abs(s[0]-z) < 1e-9]
            res.append((z, A[0] if A else [], B[0] if B else []))
        return res

    def _xor_boundary(self, A, B):
        cnt = {}
        for L in A + B:
            for u, v in self._edges(L):
                k = (min(u, v), max(u, v)); cnt[k] = cnt.get(k, 0) + 1
        return [k for k, c in cnt.items() if c % 2 == 1]

    @staticmethod
    def _chain(edges):
        adj = {}
        for u, v in edges:
            adj.setdefault(u, []).append(v); adj.setdefault(v, []).append(u)
        for k, n in adj.items():
            if len(n) != 2: raise RuntimeError("Kontur nicht sauber geschlossen (Knoten %d Grad %d)" % (k, len(n)))
        seen = set(); loops = []
        for s in adj:
            if s in seen: continue
            L = [s]; seen.add(s); prev = None; cur = s
            while True:
                n = adj[cur]; nxt = n[0] if n[0] != prev else n[1]
                if nxt == s: break
                L.append(nxt); seen.add(nxt); prev, cur = cur, nxt
            loops.append(L)
        return loops

    def build(self):
        # 1) Konformitaet: alle Randkanten muessen Delaunay-Kanten sein
        for it in range(200):
            changed = False
            for z, A, B in self._levels():
                E = self._xor_boundary(A, B)
                if not E: continue
                ids = sorted(set([u for e in E for u in e]))
                P = self._P()[ids]
                tri = Delaunay(P)
                loc = np.array(ids)[tri.simplices]
                have = set()
                for t in loc:
                    for i in range(3):
                        a, b = t[i], t[(i+1) % 3]; have.add((min(a, b), max(a, b)))
                miss = [e for e in E if e not in have]
                for a, b in miss:
                    self._split_edge(a, b); changed = True
            if not changed: break
        else:
            raise RuntimeError("Triangulierung konvergiert nicht")
        P = self._P(); tris = []
        # 2) waagrechte Flaechen
        for z, A, B in self._levels():
            E = self._xor_boundary(A, B)
            if not E: continue
            region = self._chain(E)
            ids = np.array(sorted(set([u for e in E for u in e])))
            tri = Delaunay(P[ids]); loc = ids[tri.simplices]
            cen = P[loc].mean(1)
            keep = self._contains(region, cen)
            loc = loc[keep]; cen = cen[keep]
            inA = self._contains(A, cen) if A else np.zeros(len(loc), bool)
            for t, up in zip(loc, inA):
                a, b, c = P[t[0]], P[t[1]], P[t[2]]
                cr = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
                if (cr > 0) != up: t = t[[0, 2, 1]]
                tris.append([(*P[t[0]], z), (*P[t[1]], z), (*P[t[2]], z)])
        # 3) Waende
        for z0, z1, loops in self.slabs:
            for i, L in enumerate(loops):
                xy = P[L]
                area = 0.5*np.sum(xy[:, 0]*np.roll(xy[:, 1], -1) - np.roll(xy[:, 0], -1)*xy[:, 1])
                hole = self._depth_parity(loops, i) == 1
                ccw = area > 0
                seq = L if (ccw != hole) else L[::-1]
                n = len(seq)
                for k in range(n):
                    a = P[seq[k]]; b = P[seq[(k+1) % n]]
                    tris.append([(*a, z0), (*b, z0), (*b, z1)])
                    tris.append([(*a, z0), (*b, z1), (*a, z1)])
        self.tris = np.array(tris, float)
        return self.tris

def check(t):
    from collections import Counter
    k = np.round(t, 5); E = Counter()
    for tri in k:
        for i in range(3):
            a = tuple(tri[i]); b = tuple(tri[(i+1) % 3]); E[(a, b)] += 1
    bad = sum(1 for (a, b), c in E.items() if c != 1 or E.get((b, a), 0) != 1)
    v = np.sum(np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2]))) / 6
    return bad, v

def save_stl(path, t, name):
    n = np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]); l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1; n /= l
    with open(path, 'wb') as f:
        f.write(name.encode()[:80].ljust(80, b' ')); f.write(struct.pack('<I', len(t)))
        rec = np.zeros(len(t), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
        rec['n'] = n; rec['v'] = t; f.write(rec.tobytes())

# ------------------------------------------------------------- 2D-Bausteine
def arc(cx, cy, r, a0, a1, include_end=True):
    n = max(2, int(np.ceil(abs(a1-a0)*r/SEG_MM)))
    a = np.linspace(a0, a1, n+1)
    if not include_end: a = a[:-1]
    return [(cx+r*np.cos(x), cy+r*np.sin(y_)) for x, y_ in zip(a, a)]
def circle(cx, cy, r, n=None):
    n = n or max(24, int(np.ceil(2*np.pi*r/SEG_MM)))
    a = np.linspace(0, 2*np.pi, n, endpoint=False)
    return list(zip(cx+r*np.cos(a), cy+r*np.sin(a)))
def rrect(w, h, r):
    hw, hh = w/2, h/2; pts = []
    for cx, cy, a0 in [(hw-r, hh-r, 0), (-hw+r, hh-r, np.pi/2), (-hw+r, -hh+r, np.pi), (hw-r, -hh+r, 1.5*np.pi)]:
        pts += arc(cx, cy, r, a0, a0+np.pi/2)
    return pts
def pocket_relief(s, rr):
    """Quadrat s x s mit Freistich-Boegen in den Ecken (Plexi-Ecken sind scharf)."""
    h = s/2; pts = []
    for k in range(4):
        a = k*np.pi/2
        R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        seg = arc(h, h, rr, -np.pi/2, np.pi)          # Bogen um Ecke (h,h), aussen herum
        pts += [tuple(R @ np.array(p)) for p in seg]
    return pts
def hexagon(cx, cy, af, rot=0.0):
    R = af/np.sqrt(3); a = rot + np.arange(6)*np.pi/3
    return list(zip(cx+R*np.cos(a), cy+R*np.sin(a)))
def magnet_positions():
    a = MAG_POS
    return [(a, a), (-a, a), (-a, -a), (a, -a), (0, a), (0, -a), (a, 0), (-a, 0)]
def corner_windows(m, rw):
    wins = []
    bar = 11.0; e = 92.0; fr = 4.0
    for sx, sy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        a0 = np.arcsin(bar/rw); a1 = np.pi/2 - a0
        pts = [(bar, np.sqrt(rw**2-bar**2))]
        pts += arc(bar+fr, e-fr, fr, np.pi, np.pi/2)
        pts += arc(e-fr, e-fr, fr, np.pi/2, 0)
        pts += arc(e-fr, bar+fr, fr, 0, -np.pi/2)
        pts += [(np.sqrt(rw**2-bar**2), bar)]
        pts += arc(0, 0, rw, a0, a1)[1:-1]
        pts = [(sx*x, sy*y) for x, y in pts]
        if sx*sy < 0: pts = pts[::-1]
        wins.append(m.loop(pts))
    return wins
def outline(notch_w=None):
    """Aussenkontur 216x216 mit Eckradius; an den 8 Schraubenpositionen immer Stuetzpunkte,
    mit notch_w zusaetzlich U-Taschen (von der Kante nach innen bis hinter das Schraubenloch)."""
    h = AUSSEN/2; r = ECK_R; w = MUTTER_TASCHE_B/2; side = []
    side.append((h, -h+r))
    for c in sorted([-SCHR_OFF, SCHR_OFF]):
        side.append((h, c-w))
        if notch_w:
            side.append((SCHR_POS, c-w))
            for a in np.linspace(-np.pi/2, -1.5*np.pi, 25)[1:-1]:
                side.append((SCHR_POS + w*np.cos(a), c + w*np.sin(a)))
            side.append((SCHR_POS, c+w))
        side.append((h, c+w))
    side += arc(h-r, h-r, r, 0, np.pi/2)[:-1]
    pts = []
    for k in range(4):
        a = k*np.pi/2; R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        pts += [tuple(R @ np.array(p)) for p in side]
    return pts
def screw_positions():
    p = []
    for s in (-SCHR_OFF, SCHR_OFF):
        p += [(s, SCHR_POS), (s, -SCHR_POS), (SCHR_POS, s), (-SCHR_POS, s)]
    return p

# ------------------------------------------------------------------- Teile
def frontrahmen():
    m = Mesh2p5D()
    outer = m.loop(rrect(AUSSEN, AUSSEN, ECK_R))
    holes = [m.loop(circle(x, y, SCHRAUBE_D/2, 32)) for x, y in screw_positions()]
    win = m.loop(rrect(FENSTER, FENSTER, FENSTER_R))
    pocket = m.loop(pocket_relief(PLATTE+PLATTE_SPIEL, 1.6))
    fm = [m.loop(circle(x, y, (MAG_D+MAG_SPIEL)/2, 64)) for x, y in front_magnet_positions()]
    m.slab(0, FRONT_MAG_TIEFE, [outer, win] + holes + fm)
    m.slab(FRONT_MAG_TIEFE, FRONT_LIPPE, [outer, win] + holes)
    m.slab(FRONT_LIPPE, FRONT_LIPPE+STAPEL, [outer, pocket] + holes)
    return m.build()

def tube_rings(m, ri, ro_list, extra_r):
    """liefert Funktionen fuer Vollring- und Zungen-Konturen mit identischen Stuetzpunkten."""
    radii = sorted(set([ri, ri+FASE] + ro_list + extra_r))
    phi = [2*np.pi*k/SCHLITZE + np.pi/SCHLITZE for k in range(SCHLITZE)]   # Schlitzmitten
    hw = SCHLITZ_B/2
    def ang(r, k, side):  # Winkel der Schlitzflanke k (side=-1 linke, +1 rechte Flanke) bei Radius r
        return phi[k] + side*np.arcsin(hw/r)
    def finger_arc(r, k):  # von Flanke rechts von Schlitz k bis Flanke links von Schlitz k+1
        a0 = ang(r, k, +1); a1 = ang(r, (k+1) % SCHLITZE, -1)
        if a1 < a0: a1 += 2*np.pi
        n = max(2, int(np.ceil((a1-a0)*r/SEG_MM)))
        return [(r*np.cos(a), r*np.sin(a)) for a in np.linspace(a0, a1, n+1)]
    def slot_arc(r, k):
        a0 = ang(r, k, -1); a1 = ang(r, k, +1)
        return [(r*np.cos(a), r*np.sin(a)) for a in np.linspace(a0, a1, 3)]
    def full(r):
        pts = []
        for k in range(SCHLITZE):
            pts += slot_arc(r, k)[:-1]
            pts += finger_arc(r, k)[:-1]
        return m.loop(pts)
    def side(k, s, r0, r1):  # Flankenpunkte von r0 nach r1 inkl. aller Zwischenradien
        rs = [r for r in radii if min(r0, r1)-1e-9 <= r <= max(r0, r1)+1e-9]
        if r0 > r1: rs = rs[::-1]
        return [(r*np.cos(ang(r, k, s)), r*np.sin(ang(r, k, s))) for r in rs]
    def fingers(rin, rout):
        out = []
        for k in range(SCHLITZE):
            k2 = (k+1) % SCHLITZE
            pts = finger_arc(rout, k)                      # aussen, CCW
            pts += side(k2, -1, rout, rin)[1:]             # linke Flanke Schlitz k+1 nach innen
            pts += finger_arc(rin, k)[::-1][1:]            # innen zurueck
            pts += side(k, +1, rin, rout)[1:-1]            # rechte Flanke Schlitz k nach aussen
            out.append(m.loop(pts))
        return out
    return full, fingers

def traeger(passring=False):
    m = Mesh2p5D()
    ri = (GLB_D + SPIEL_D)/2
    ro = ri + ROHR_WAND
    rg = ro - NUT_TIEFE
    full, fingers = tube_rings(m, ri, [ro, rg], [])
    if passring:
        m.slab(0, PASSRING_H-1.5, [full(ro), full(ri)])
        m.slab(PASSRING_H-1.5, PASSRING_H, [full(ro), full(ri+FASE)])
        return m.build()
    outer = m.loop(outline())
    outer_n = m.loop(outline(True))
    ap = m.loop(circle(0, 0, ri-LIPPE))
    holes = [m.loop(circle(x, y, SCHRAUBE_D/2, 32)) for x, y in screw_positions()]
    wins = corner_windows(m, ro + 7.0)          # Leichtbau-Fenster, Lichtweg unberuehrt
    mags = [m.loop(circle(x, y, (MAG_D+MAG_SPIEL)/2, 64)) for x, y in magnet_positions()]
    zm = MAG_H + 0.1
    # Ueberstand Schraube hinter dem Rueckrahmen = Laenge - Frontrahmen - Rueckrahmen (+0,4 Luft)
    zn = SCHR_LAENGE - (FRONT_LIPPE + STAPEL) - RUECK_DICKE + 0.4
    cuts = sorted(set([0, zm, zn, FLANSCH]))
    for a, b in zip(cuts[:-1], cuts[1:]):
        L = [outer_n if b <= zn + 1e-9 else outer, ap] + wins
        if b > zn + 1e-9: L += holes
        if b <= zm + 1e-9: L += mags
        m.slab(a, b, L)
    z = FLANSCH
    zs = z + SCHLITZ_START
    g0, g1 = z + NUT_Z[0], z + NUT_Z[1]
    ztop = z + ROHR_LAENGE
    m.slab(z, zs, [full(ro), full(ri)])
    cuts = sorted(set([zs, g0, g1, ztop-1.5, ztop]))
    for a, b in zip(cuts[:-1], cuts[1:]):
        rout = rg if (a >= g0-1e-9 and b <= g1+1e-9) else ro
        rin = ri + FASE if a >= ztop-1.5-1e-9 else ri
        m.slab(a, b, fingers(rin, rout))
    return m.build()

def rueckrahmen():
    """Hinterer Deckel des Filterpakets. Druck: Plexi-Seite aufs Bett, Magnetseite + Zentrierring oben."""
    m = Mesh2p5D()
    ri = (GLB_D + SPIEL_D)/2
    r_ap = ri - LIPPE                     # Flanschoeffnung im Traeger
    rz_o = r_ap - ZENTRIER_SP; rz_i = rz_o - 2.0
    outer = m.loop(outline())
    ap = m.loop(circle(0, 0, rz_i))
    ring_o = m.loop(circle(0, 0, rz_o))
    ins = [m.loop(circle(x, y, SCHRAUBE_D/2, 32)) for x, y in screw_positions()]
    wins = corner_windows(m, ri + ROHR_WAND + 7.0)
    mags = [m.loop(circle(x, y, (MAG_D+MAG_SPIEL)/2, 64)) for x, y in magnet_positions()]
    zm = RUECK_DICKE - (MAG_H + 0.1)
    m.slab(0, zm, [outer, ap] + ins + wins)
    m.slab(zm, RUECK_DICKE, [outer, ap] + ins + wins + mags)
    m.slab(RUECK_DICKE, RUECK_DICKE + ZENTRIER_H, [ring_o, ap])
    return m.build()

# --- Frontdeckel-Magnete (v4): 4 Magnete in den Ecken der vorderen Lippe des Frontrahmens
FRONT_MAG_POS   = 96.0  # Mittelpunkt (+-x, +-y), zwischen Fensterecke und Rahmenecke
FRONT_MAG_TIEFE = 2.0   # Tasche im Frontrahmen (Lippe 2,5 -> 0,5 mm Boden zum Plexi); Magnet steht 1 mm vor
def front_magnet_positions():
    a = FRONT_MAG_POS
    return [(a, a), (-a, a), (-a, -a), (a, -a)]

# ------------------------------------------------- Transport-Schutzdeckel
DECKEL_DICKE = 5.0     # Rueckdeckel
FRONTDECKEL_DICKE = 6.0  # Frontdeckel (Magnettaschen 4,2 tief -> 1,8 mm Boden)
KOPF_H       = 3.3     # Tasche fuer Schraubenkoepfe (DIN 912: D5,5 x 3,0 / ISO 7380: D5,7 x 1,65), Breite = MUTTER_TASCHE_B
ZAPFEN_SP    = 0.15    # Spiel je Seite: Frontdeckel-Zapfen im Fenster (Reibschluss)
ZAPFEN_H     = 2.0     # Fensterlippe ist 2,5 tief -> 0,5 mm Luft zum Plexi

def rueckdeckel():
    """Schutzplatte hinten, haelt magnetisch am Rueckrahmen (Magnete gepolt wie im Traeger).
    Druck: Magnetseite aufs Bett."""
    m = Mesh2p5D()
    ri = (GLB_D + SPIEL_D)/2
    r_ap = ri - LIPPE
    outer = m.loop(outline()); outer_n = m.loop(outline(True))
    rec = m.loop(circle(0, 0, r_ap))                   # Vertiefung fuer den Zentrierring
    mags = [m.loop(circle(x, y, (MAG_D+MAG_SPIEL)/2, 64)) for x, y in magnet_positions()]
    zr = ZENTRIER_H + 0.4
    zm = MAG_H + 0.1
    zn = SCHR_LAENGE - (FRONT_LIPPE + STAPEL) - RUECK_DICKE + 0.4
    cuts = sorted(set([0, zr, zm, zn, DECKEL_DICKE]))
    for a, b in zip(cuts[:-1], cuts[1:]):
        L = [outer_n if b <= zn + 1e-9 else outer]
        if b <= zr + 1e-9: L.append(rec)
        if b <= zm + 1e-9: L += mags
        m.slab(a, b, L)
    return m.build()

def frontdeckel():
    """Schutzplatte vorne (Sonnenseite): Zapfen klemmt im Fenster des Frontrahmens.
    Druck: Aussenseite aufs Bett, Zapfen oben."""
    m = Mesh2p5D()
    outer = m.loop(outline()); outer_n = m.loop(outline(True))   # U-Taschen fuer die Schraubenkoepfe
    plug = m.loop(rrect(FENSTER-2*ZAPFEN_SP, FENSTER-2*ZAPFEN_SP, FENSTER_R-ZAPFEN_SP))
    D = FRONTDECKEL_DICKE
    fm = [m.loop(circle(x, y, (MAG_D+MAG_SPIEL)/2, 64)) for x, y in front_magnet_positions()]
    vor = MAG_H - FRONT_MAG_TIEFE                      # Ueberstand der Frontrahmen-Magnete
    zt = D - (MAG_H + vor + 0.2)                       # eigener Magnet unten, Gegenmagnet greift oben hinein
    zk = D - KOPF_H
    cuts = sorted(set([0, zt, zk, D]))
    for a, b in zip(cuts[:-1], cuts[1:]):
        L = [outer_n if a >= zk - 1e-9 else outer]
        if a >= zt - 1e-9: L += fm
        m.slab(a, b, L)
    m.slab(D, D + ZAPFEN_H, [plug])
    return m.build()

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, fn in [('solarfilter_frontrahmen', frontrahmen),
                     ('solarfilter_rueckrahmen', rueckrahmen),
                     ('solarfilter_traeger', traeger),
                     ('solarfilter_passring', lambda: traeger(True)),
                     ('solarfilter_schutz_rueckdeckel', rueckdeckel),
                     ('solarfilter_schutz_frontdeckel', frontdeckel)]:
        t = fn(); bad, vol = check(t)
        save_stl(os.path.join(out, name+'.stl'), t, name)
        mn, mx = t.reshape(-1, 3).min(0), t.reshape(-1, 3).max(0)
        print(f"{name}: {len(t)} Dreiecke, Volumen {vol/1000:.1f} cm3, offene/fehlerhafte Kanten: {bad}, "
              f"Masse {mx[0]-mn[0]:.1f} x {mx[1]-mn[1]:.1f} x {mx[2]-mn[2]:.1f}")

import FreeCAD as App
import FreeCADGui as Gui
import Part
import math

doc = App.ActiveDocument

# ============================================================
# 設定
# ============================================================

GAP = 15.0
TOL = 1e-7


# ============================================================
# 選択
# ============================================================

sel = Gui.Selection.getSelectionEx()

if not sel:
    raise Exception("BodyのFaceを1枚選択してください")

source = None
base_face = None

for s in sel:

    obj = s.Object

    if hasattr(obj, "Shape") and source is None:
        source = obj

    for sub in s.SubElementNames:

        if sub.startswith("Face"):

            try:
                index = int(sub.replace("Face", "")) - 1

                if 0 <= index < len(obj.Shape.Faces):
                    base_face = obj.Shape.Faces[index]

            except:
                pass


if source is None:
    raise Exception("Bodyを選択してください")

if base_face is None:
    raise Exception("基準Faceを1枚選択してください")

shape = source.Shape


# ============================================================
# 既存ProjectedFace削除
# ============================================================

for obj in list(doc.Objects):

    try:
        if obj.Name.startswith("ProjectedFace"):
            doc.removeObject(obj.Name)
    except ReferenceError:
        pass

doc.recompute()


# ============================================================
# Face法線
# ============================================================

def get_face_normal(face):

    try:
        c = face.CenterOfMass
        u, v = face.Surface.parameter(c)

        n = face.normalAt(u, v)
        n.normalize()

        return n

    except:
        pass

    if face.Vertexes:

        try:
            p = face.Vertexes[0].Point
            u, v = face.Surface.parameter(p)

            n = face.normalAt(u, v)
            n.normalize()

            return n

        except:
            pass

    return None


front_normal = get_face_normal(base_face)

if front_normal is None:
    raise Exception("基準Faceの法線を取得できません")


# ============================================================
# 基準Face Right
# ============================================================

front_right = None

for edge in base_face.Edges:

    if isinstance(edge.Curve, Part.Line):

        if len(edge.Vertexes) >= 2:

            p1 = edge.Vertexes[0].Point
            p2 = edge.Vertexes[-1].Point

            v = p2 - p1

            if v.Length > TOL:

                v.normalize()

                if abs(v.dot(front_normal)) < TOL:

                    front_right = v
                    break


if front_right is None:
    raise Exception("基準Faceの横方向を決定できません")


# ============================================================
# 基準Face Up
# ============================================================

front_up = front_normal.cross(front_right)
front_up.normalize()


# ============================================================
# 原点
# ============================================================

origin = base_face.CenterOfMass


print("")
print("========================================")
print("基準Face")
print("========================================")
print("Normal =", front_normal)
print("Right  =", front_right)
print("Up     =", front_up)
print("Origin =", origin)


# ============================================================
# 3D → 2D
# ============================================================

def project_point(p, right, up):

    v = p - origin

    return App.Vector(
        v.dot(right),
        v.dot(up),
        0
    )


# ============================================================
# Edge KEY
# ============================================================

def point_key(p):

    return (
        round(p.x, 7),
        round(p.y, 7)
    )


def edge_key(edge, right, up):

    try:

        # ----------------------------------------------------
        # LINE
        # ----------------------------------------------------

        if isinstance(edge.Curve, Part.Line):

            if len(edge.Vertexes) < 2:
                return None

            p1 = project_point(
                edge.Vertexes[0].Point,
                right,
                up
            )

            p2 = project_point(
                edge.Vertexes[-1].Point,
                right,
                up
            )

            k1 = point_key(p1)
            k2 = point_key(p2)

            if k1 > k2:
                k1, k2 = k2, k1

            return (
                "LINE",
                k1,
                k2
            )


        # ----------------------------------------------------
        # CIRCLE
        # ----------------------------------------------------

        if isinstance(edge.Curve, Part.Circle):

            c = project_point(
                edge.Curve.Center,
                right,
                up
            )

            return (
                "CIRCLE",
                round(c.x, 7),
                round(c.y, 7),
                round(edge.Curve.Radius, 7)
            )

    except:
        pass

    return None


# ============================================================
# LINE
# ============================================================

def project_line(edge, right, up):

    if len(edge.Vertexes) < 2:
        return None

    p1 = edge.Vertexes[0].Point
    p2 = edge.Vertexes[-1].Point

    q1 = project_point(
        p1,
        right,
        up
    )

    q2 = project_point(
        p2,
        right,
        up
    )

    if (q2 - q1).Length < TOL:
        return None

    return Part.makeLine(q1, q2)


# ============================================================
# CIRCLE
# ============================================================

def project_circle(edge, right, up):

    curve = edge.Curve

    center = curve.Center
    radius = curve.Radius

    axis = curve.Axis
    axis.normalize()

    view_normal = right.cross(up)
    view_normal.normalize()


    # --------------------------------------------------------
    # 正面から見る → 円
    # --------------------------------------------------------

    if abs(abs(axis.dot(view_normal)) - 1.0) < TOL:

        c = project_point(
            center,
            right,
            up
        )

        return Part.makeCircle(
            radius,
            c,
            App.Vector(0, 0, 1)
        )


    # --------------------------------------------------------
    # 真横から見る → 直径線
    # --------------------------------------------------------

    if abs(axis.dot(view_normal)) < TOL:

        radial = axis.cross(right)

        if radial.Length < TOL:
            radial = axis.cross(up)

        if radial.Length < TOL:
            return None

        radial.normalize()

        p1 = center + radial * radius
        p2 = center - radial * radius

        q1 = project_point(
            p1,
            right,
            up
        )

        q2 = project_point(
            p2,
            right,
            up
        )

        if (q2 - q1).Length < TOL:
            return None

        return Part.makeLine(q1, q2)


    return None


# ============================================================
# ARC
# ============================================================

def project_arc(edge, right, up):

    curve = edge.Curve

    axis = curve.Axis
    axis.normalize()

    view_normal = right.cross(up)
    view_normal.normalize()


    if abs(abs(axis.dot(view_normal)) - 1.0) >= TOL:
        return None

    if len(edge.Vertexes) < 2:
        return None


    center = project_point(
        curve.Center,
        right,
        up
    )

    p1 = project_point(
        edge.Vertexes[0].Point,
        right,
        up
    )

    p2 = project_point(
        edge.Vertexes[-1].Point,
        right,
        up
    )


    a1 = math.atan2(
        p1.y - center.y,
        p1.x - center.x
    )

    a2 = math.atan2(
        p2.y - center.y,
        p2.x - center.x
    )


    circle = Part.Circle(
        center,
        App.Vector(0, 0, 1),
        curve.Radius
    )

    arc = Part.ArcOfCircle(
        circle,
        a1,
        a2
    )

    return arc.toShape()


# ============================================================
# Edge投影
# ============================================================

def project_edge(edge, right, up):

    curve = edge.Curve

    if isinstance(curve, Part.Line):

        return project_line(
            edge,
            right,
            up
        )


    if isinstance(curve, Part.Circle):

        if edge.isClosed():

            return project_circle(
                edge,
                right,
                up
            )

        return project_arc(
            edge,
            right,
            up
        )


    return None


# ============================================================
# 投影Shape作成
# ============================================================

def make_projection_shape(right, up):

    edges2d = []
    used = set()

    for face in shape.Faces:

        for edge in face.Edges:

            key = edge_key(
                edge,
                right,
                up
            )

            if key is not None:

                if key in used:
                    continue

                used.add(key)


            result = project_edge(
                edge,
                right,
                up
            )

            if result is not None:
                edges2d.append(result)


    if not edges2d:
        return None

    return Part.makeCompound(edges2d)


# ============================================================
# ★ 5方向の座標系
# ============================================================

views = [

    (
        "正面図",
        front_right,
        front_up
    ),

    (
        "上面図",
        front_right,
        front_normal
    ),

    (
        "下面図",
        front_right,
        -front_normal
    ),

    (
        "右側面図",
        -front_normal,
        front_up
    ),

    (
        "左側面図",
        front_normal,
        front_up
    )
]


# ============================================================
# 5面を必ず作成
# ============================================================

objects = {}

for name, right, up in views:

    print("")
    print("----------------------------------------")
    print(name)
    print("Right =", right)
    print("Up    =", up)
    print("----------------------------------------")


    projected = make_projection_shape(
        right,
        up
    )


    if projected is None:

        print(
            "★★★",
            name,
            "のShapeが作れませんでした"
        )

        continue


    obj = doc.addObject(
        "Part::Feature",
        "ProjectedFace"
    )

    obj.Label = (
        "ProjectedFace_" + name
    )

    obj.Shape = projected

    obj.Placement = App.Placement(
        App.Vector(0, 0, 0),
        App.Rotation()
    )

    objects[name] = obj

    print(
        "作成OK:",
        obj.Name,
        "Edges =",
        len(projected.Edges)
    )


doc.recompute()


# ============================================================
# 基準Faceの2D範囲
# ============================================================

base_min_x = float("inf")
base_max_x = float("-inf")
base_min_y = float("inf")
base_max_y = float("-inf")


for edge in base_face.Edges:

    for vertex in edge.Vertexes:

        p = project_point(
            vertex.Point,
            front_right,
            front_up
        )

        base_min_x = min(base_min_x, p.x)
        base_max_x = max(base_max_x, p.x)

        base_min_y = min(base_min_y, p.y)
        base_max_y = max(base_max_y, p.y)


    if isinstance(edge.Curve, Part.Circle):

        c = project_point(
            edge.Curve.Center,
            front_right,
            front_up
        )

        r = edge.Curve.Radius

        base_min_x = min(
            base_min_x,
            c.x - r
        )

        base_max_x = max(
            base_max_x,
            c.x + r
        )

        base_min_y = min(
            base_min_y,
            c.y - r
        )

        base_max_y = max(
            base_max_y,
            c.y + r
        )


# ============================================================
# Placement用Bounds
# ============================================================

bounds = {}

for name, obj in objects.items():

    bb = obj.Shape.BoundBox

    bounds[name] = (
        bb.XMin,
        bb.XMax,
        bb.YMin,
        bb.YMax
    )


# ============================================================
# 正面
# ============================================================

if "正面図" in objects:

    objects["正面図"].Placement.Base = App.Vector(
        0,
        0,
        0
    )


# ============================================================
# 上面
# ============================================================

if "上面図" in objects:

    xmin, xmax, ymin, ymax = bounds["上面図"]

    shift_y = (
        base_max_y
        + GAP
        - ymin
    )

    objects["上面図"].Placement.Base = App.Vector(
        0,
        shift_y,
        0
    )


# ============================================================
# 下面
# ============================================================

if "下面図" in objects:

    xmin, xmax, ymin, ymax = bounds["下面図"]

    shift_y = (
        base_min_y
        - GAP
        - ymax
    )

    objects["下面図"].Placement.Base = App.Vector(
        0,
        shift_y,
        0
    )


# ============================================================
# 右側面
# ============================================================

if "右側面図" in objects:

    xmin, xmax, ymin, ymax = bounds["右側面図"]

    shift_x = (
        base_max_x
        + GAP
        - xmin
    )

    objects["右側面図"].Placement.Base = App.Vector(
        shift_x,
        0,
        0
    )


# ============================================================
# 左側面
# ============================================================

if "左側面図" in objects:

    xmin, xmax, ymin, ymax = bounds["左側面図"]

    shift_x = (
        base_min_x
        - GAP
        - xmax
    )

    objects["左側面図"].Placement.Base = App.Vector(
        shift_x,
        0,
        0
    )


# ============================================================
# 更新
# ============================================================

doc.recompute()


# ============================================================
# 表示
# ============================================================

for obj in objects.values():

    obj.ViewObject.Visibility = True


Gui.activeDocument().activeView().fitAll()


# ============================================================
# 結果確認
# ============================================================

print("")
print("")
print("========================================")
print("★★★★★ 5面出力結果 ★★★★★")
print("========================================")

for name in [
    "正面図",
    "上面図",
    "下面図",
    "右側面図",
    "左側面図"
]:

    if name in objects:

        obj = objects[name]

        print(
            "○",
            name,
            "=>",
            obj.Name,
            "Edges =",
            len(obj.Shape.Edges)
        )

    else:

        print(
            "×",
            name,
            "=> 作成されていません"
        )

print("")
print("配置間隔 =", GAP, "mm")
print("========================================")
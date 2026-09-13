import FreeCAD as App
import FreeCADGui as Gui
import Draft
import Part


doc = App.ActiveDocument


# ============================================================
# 設定
# ============================================================

SOURCE_PREFIX = "ProjectedFace"
LAYER_PREFIX = "DraftLayer_"
DRAFT_LINE_PREFIX = "DraftLine_"
DRAFT_CIRCLE_PREFIX = "DraftCircle_"


# ============================================================
# 対象となるProjectedFaceを取得
# ============================================================

source_objects = []

for obj in list(doc.Objects):

    try:

        if obj.Name.startswith(
            SOURCE_PREFIX
        ):

            source_objects.append(obj)

    except ReferenceError:

        pass


if not source_objects:

    raise Exception(
        "ProjectedFace が見つかりません。\n"
        "先に zumen5face.py を実行してください。"
    )


print("")
print("========================================")
print("ProjectedFace 検出")
print("========================================")


for obj in source_objects:

    print(
        obj.Name,
        " / ",
        obj.Label
    )


# ============================================================
# Layer名を決定
# ============================================================

def get_layer_name(obj):

    label = obj.Label

    if "正面" in label:
        return "正面図"

    if "上面" in label:
        return "上面図"

    if "下面" in label:
        return "下面図"

    if "右側面" in label:
        return "右側面図"

    if "左側面" in label:
        return "左側面図"

    return label


# ============================================================
# 既存Layerを削除
#
# このマクロで作ったLayerのみ
# ============================================================

for obj in list(doc.Objects):

    try:

        if obj.Name.startswith(
            LAYER_PREFIX
        ):

            doc.removeObject(
                obj.Name
            )

    except ReferenceError:

        pass


doc.recompute()


# ============================================================
# 既存のDraft Line / Circleを削除
#
# このマクロで作ったもののみ
# ============================================================

for obj in list(doc.Objects):

    try:

        if (
            obj.Name.startswith(
                DRAFT_LINE_PREFIX
            )
            or
            obj.Name.startswith(
                DRAFT_CIRCLE_PREFIX
            )
        ):

            doc.removeObject(
                obj.Name
            )

    except ReferenceError:

        pass


doc.recompute()


# ============================================================
# ShapeのPlacementを反映した点を取得
# ============================================================

def transform_point(
    obj,
    p
):

    return obj.Placement.multVec(
        p
    )


# ============================================================
# Layer作成
# ============================================================

layers = {}


def get_or_create_layer(
    layer_name
):

    if layer_name in layers:

        return layers[
            layer_name
        ]


    layer = Draft.make_layer(
        name=layer_name,
        line_width=2.0
    )


    if layer is None:

        raise Exception(
            "Draft Layerを作成できません: "
            + layer_name
        )


    layer.Label = layer_name


    layers[
        layer_name
    ] = layer


    return layer


# ============================================================
# Shape Edge → Draft Line / Draft Circle
# ============================================================

def convert_edge_to_draft(
    source_obj,
    edge,
    layer,
    counter
):

    # ========================================================
    # LINE
    # ========================================================

    if isinstance(
        edge.Curve,
        Part.Line
    ):

        if len(edge.Vertexes) < 2:

            return None


        p1 = transform_point(
            source_obj,
            edge.Vertexes[0].Point
        )

        p2 = transform_point(
            source_obj,
            edge.Vertexes[-1].Point
        )


        if (
            p2 - p1
        ).Length < 1e-9:

            return None


        line = Draft.make_line(
            p1,
            p2
        )


        if line is None:

            return None


        line.Label = (
            "DraftLine_%s_%04d"
            % (
                layer.Label,
                counter
            )
        )


        return line


    # ========================================================
    # CIRCLE
    #
    # 円はDraft Circle
    # ========================================================

    if isinstance(
        edge.Curve,
        Part.Circle
    ):

        curve = edge.Curve


        center = transform_point(
            source_obj,
            curve.Center
        )


        radius = curve.Radius


        circle = Draft.make_circle(
            radius=radius,
            placement=App.Placement(
                center,
                App.Rotation()
            ),
            face=False
        )


        if circle is None:

            return None


        circle.Label = (
            "DraftCircle_%s_%04d"
            % (
                layer.Label,
                counter
            )
        )


        return circle


    # ========================================================
    # その他
    #
    # ポリライン化しない
    # ========================================================

    print(
        "  未対応Curve:",
        type(edge.Curve).__name__
    )


    return None


# ============================================================
# 各ProjectedFaceを変換
# ============================================================

total_lines = 0
total_circles = 0


for source_obj in source_objects:

    layer_name = get_layer_name(
        source_obj
    )


    print("")
    print("----------------------------------------")
    print(
        "処理:",
        source_obj.Label
    )
    print(
        "Layer:",
        layer_name
    )
    print("----------------------------------------")


    # ========================================================
    # Layer
    # ========================================================

    layer = get_or_create_layer(
        layer_name
    )


    created = []


    # ========================================================
    # Shapeの全Edge
    # ========================================================

    for index, edge in enumerate(
        source_obj.Shape.Edges,
        1
    ):


        result = convert_edge_to_draft(
            source_obj,
            edge,
            layer,
            index
        )


        if result is None:

            continue


        created.append(
            result
        )


        # ----------------------------------------------------
        # 作成数カウント
        # ----------------------------------------------------

        try:

            if result.Name.startswith(
                DRAFT_CIRCLE_PREFIX
            ):

                total_circles += 1

            else:

                total_lines += 1

        except:

            total_lines += 1


    # ========================================================
    # Layerへ追加
    # ========================================================

    if created:

        old_group = list(
            layer.Group
        )

        layer.Group = (
            old_group
            + created
        )


    print(
        "作成数 =",
        len(created)
    )


# ============================================================
# 元ProjectedFaceを削除
#
# Draft化が完了してから削除
#
# 元の3Dパーツは削除しない
# ============================================================

print("")
print("========================================")
print("ProjectedFace削除")
print("========================================")


for source_obj in list(
    source_objects
):

    try:

        name = source_obj.Name
        label = source_obj.Label


        if doc.getObject(
            name
        ) is not None:

            print(
                "削除:",
                name,
                "/",
                label
            )


            doc.removeObject(
                name
            )


    except ReferenceError:

        pass


# ============================================================
# 更新
# ============================================================

doc.recompute()


# ============================================================
# Draft Layerを表示
# ============================================================

for layer in layers.values():

    layer.ViewObject.Visibility = True


# ============================================================
# 表示更新
# ============================================================

Gui.activeDocument().activeView().fitAll()


# ============================================================
# 完了
# ============================================================

print("")
print("========================================")
print("ProjectedFace → Draft Layer / Line 完了")
print("========================================")


print(
    "Layer数 =",
    len(layers)
)


for name, layer in layers.items():

    print(
        name,
        "=>",
        layer.Name,
        "Object数 =",
        len(layer.Group)
    )


print("")
print(
    "Draft Line数   =",
    total_lines
)

print(
    "Draft Circle数 =",
    total_circles
)

print("")
print(
    "Draft変換完了"
)

print(
    "元ProjectedFace = 削除"
)

print(
    "元の3Dパーツ = そのまま"
)

print("")
print("========================================")
# ============================================================
# 指定角度でDraft図面全体を回転
#
# part_zumen_main.py から
# ROTATION_ANGLE が渡される
#
# 例：
#   90   → 反時計回り90°
#   -90  → 時計回り90°
#   45   → 反時計回り45°
#   0    → 回転なし
# ============================================================

try:

    rotation_angle = float(
        ROTATION_ANGLE
    )

except:

    rotation_angle = 0.0


print("")
print("========================================")
print("Draft図面回転")
print("========================================")
print(
    "回転角度 =",
    rotation_angle,
    "deg"
)


# ============================================================
# 回転対象
#
# 今回作成した5つのLayer
# ============================================================

rotation = App.Rotation(
    App.Vector(
        0,
        0,
        1
    ),
    rotation_angle
)


# ============================================================
# 全Draftオブジェクトを回転
#
# Layerではなく、Layer内の
# Draft Line / Draft Circleそのものを回転
# ============================================================

rotated_objects = []


# ============================================================
# 全LayerからDraftオブジェクトを取得
# ============================================================

for layer_name, layer in layers.items():

    try:

        for obj in list(layer.Group):

            if obj not in rotated_objects:

                rotated_objects.append(obj)

    except Exception as e:

        print(
            "Layer取得エラー:",
            layer.Label,
            e
        )


# ============================================================
# Draftオブジェクトを指定角度で回転
# ============================================================

for obj in rotated_objects:

    try:

        # ----------------------------------------------------
        # 現在のPlacement
        # ----------------------------------------------------

        old_base = obj.Placement.Base
        old_rot = obj.Placement.Rotation


        # ----------------------------------------------------
        # 原点を中心に位置を回転
        # ----------------------------------------------------

        new_base = rotation.multVec(
            old_base
        )


        # ----------------------------------------------------
        # オブジェクト自身の向きも回転
        # ----------------------------------------------------

        new_rot = rotation.multiply(
            old_rot
        )


        # ----------------------------------------------------
        # Placement更新
        # ----------------------------------------------------

        obj.Placement = App.Placement(
            new_base,
            new_rot
        )


        print(
            "回転:",
            obj.Name,
            "/",
            obj.Label
        )


    except Exception as e:

        print(
            "オブジェクト回転エラー:",
            obj.Name,
            e
        )


# ============================================================
# LayerのPlacementは回さない
# ============================================================

for layer_name, layer in layers.items():

    try:

        layer.Placement = App.Placement()

    except Exception:

        pass


# ============================================================
# 更新
# ============================================================

doc.recompute()

Gui.activeDocument().activeView().fitAll()


print("")
print(
    "Draftオブジェクト全体を",
    rotation_angle,
    "°回転しました"
)
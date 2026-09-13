import FreeCAD as App
import FreeCADGui as Gui
import Part


doc = App.ActiveDocument


# ============================================================
# 設定
# ============================================================

# 座標判定許容値(mm)
TOL = 0.001


# ============================================================
# 選択取得
# ============================================================

selection = Gui.Selection.getSelection()

if not selection:
    raise Exception("オブジェクトを選択してください。")


# ============================================================
# ベクトル計算
# ============================================================

def vector_length(v):

    return v.Length


def normalize_vector(v):

    if v.Length == 0:
        return None

    return v.normalize()


# ============================================================
# 点が同一直線上にあるか判定
# ============================================================

def is_point_on_line(point, line_start, line_end):

    direction = line_end.sub(line_start)

    if direction.Length < TOL:
        return False

    to_point = point.sub(line_start)

    # 外積の長さで距離を判定
    cross = direction.cross(to_point)

    distance = cross.Length / direction.Length

    return distance <= TOL


# ============================================================
# 2本の線が同一直線上か判定
# ============================================================

def are_collinear(line1, line2):

    p1 = line1["start"]
    p2 = line1["end"]

    p3 = line2["start"]
    p4 = line2["end"]

    direction1 = p2.sub(p1)
    direction2 = p4.sub(p3)


    if direction1.Length < TOL:
        return False

    if direction2.Length < TOL:
        return False


    # 平行か確認
    cross = direction1.cross(direction2)

    if cross.Length > TOL:
        return False


    # line2の始点がline1の直線上にあるか
    return is_point_on_line(
        p3,
        p1,
        p2
    )


# ============================================================
# 線分の範囲を取得
#
# 同一直線上の座標として計算
# ============================================================

def get_projection_range(line, origin, direction):

    start_value = (
        line["start"]
        .sub(origin)
        .dot(direction)
    )

    end_value = (
        line["end"]
        .sub(origin)
        .dot(direction)
    )

    return (
        min(start_value, end_value),
        max(start_value, end_value)
    )


# ============================================================
# 色を赤にする
# ============================================================

def set_red(obj):

    try:

        obj.ViewObject.LineColor = (
            1.0,
            0.0,
            0.0
        )

    except:

        pass


# ============================================================
# 削除対象
# ============================================================

objects_to_delete = set()


# ============================================================
# 選択したオブジェクトから
# すべての直線Edgeを取得
# ============================================================

lines = []


for obj in selection:

    if not hasattr(obj, "Shape"):
        continue


    try:

        edges = obj.Shape.Edges

    except:

        continue


    for edge in edges:

        try:

            # 直線以外は無視
            if not isinstance(
                edge.Curve,
                Part.Line
            ):
                continue


            if len(edge.Vertexes) < 2:
                continue


            start = edge.Vertexes[0].Point
            end = edge.Vertexes[-1].Point


            # 長さ
            length = start.distanceToPoint(end)


            if length < TOL:
                continue


            lines.append({

                "object": obj,
                "edge": edge,

                "start": start,
                "end": end,

                "length": length

            })


        except:

            continue


# ============================================================
# 線の本数確認
# ============================================================

App.Console.PrintMessage(
    f"解析する直線: {len(lines)} 本\n"
)


# ============================================================
# 線を総当たり比較
# ============================================================

for i in range(len(lines)):

    line1 = lines[i]

    obj1 = line1["object"]


    if obj1 in objects_to_delete:
        continue


    for j in range(i + 1, len(lines)):

        line2 = lines[j]

        obj2 = line2["object"]


        if obj2 in objects_to_delete:
            continue


        # ====================================================
        # 同じオブジェクト同士は比較しない
        # ====================================================

        if obj1 == obj2:
            continue


        # ====================================================
        # 同一直線上でなければ無視
        # ====================================================

        if not are_collinear(
            line1,
            line2
        ):
            continue


        # ====================================================
        # 基準方向
        # ====================================================

        origin = line1["start"]

        direction = (
            line1["end"]
            .sub(line1["start"])
        )

        if direction.Length < TOL:
            continue

        direction.normalize()


        # ====================================================
        # それぞれの線分範囲
        # ====================================================

        min1, max1 = get_projection_range(
            line1,
            origin,
            direction
        )

        min2, max2 = get_projection_range(
            line2,
            origin,
            direction
        )


        # ====================================================
        # 重なり範囲
        # ====================================================

        overlap_start = max(
            min1,
            min2
        )

        overlap_end = min(
            max1,
            max2
        )

        overlap_length = (
            overlap_end - overlap_start
        )


        # ====================================================
        # 重なっていない
        # ====================================================

        if overlap_length <= TOL:
            continue


        # ====================================================
        # 完全重複または完全内包
        # ====================================================

        line1_contains_line2 = (
            min1 <= min2 + TOL
            and
            max1 >= max2 - TOL
        )

        line2_contains_line1 = (
            min2 <= min1 + TOL
            and
            max2 >= max1 - TOL
        )


        # ----------------------------------------------------
        # 完全に同じ線
        # ----------------------------------------------------

        if (
            line1_contains_line2
            and
            line2_contains_line1
        ):

            # 長さが同じなら後の線を削除
            objects_to_delete.add(
                obj2
            )

            App.Console.PrintMessage(
                f"完全重複 削除: {obj2.Name}\n"
            )

            continue


        # ----------------------------------------------------
        # line1がline2を完全に内包
        # → line2を削除
        # ----------------------------------------------------

        if line1_contains_line2:

            objects_to_delete.add(
                obj2
            )

            App.Console.PrintMessage(
                f"内包 削除: {obj2.Name}\n"
            )

            continue


        # ----------------------------------------------------
        # line2がline1を完全に内包
        # → line1を削除
        # ----------------------------------------------------

        if line2_contains_line1:

            objects_to_delete.add(
                obj1
            )

            App.Console.PrintMessage(
                f"内包 削除: {obj1.Name}\n"
            )

            break


        # ====================================================
        # 一部分だけ重複
        #
        # 削除せず赤色
        # ====================================================

        set_red(obj1)
        set_red(obj2)

        App.Console.PrintMessage(
            f"部分重複 赤色: "
            f"{obj1.Name} / "
            f"{obj2.Name}\n"
        )


# ============================================================
# 重複オブジェクト削除
# ============================================================

delete_count = 0


for obj in objects_to_delete:

    try:

        # まだ存在する場合のみ削除
        if doc.getObject(obj.Name):

            doc.removeObject(
                obj.Name
            )

            delete_count += 1


    except Exception as e:

        App.Console.PrintMessage(
            f"削除エラー: {e}\n"
        )


# ============================================================
# 再計算
# ============================================================

doc.recompute()


# ============================================================
# 完了
# ============================================================

App.Console.PrintMessage(
    "\n========================================\n"
)

App.Console.PrintMessage(
    f"削除した重複線: {delete_count} 本\n"
)

App.Console.PrintMessage(
    "部分重複の線は赤色です。\n"
)

App.Console.PrintMessage(
    "========================================\n"
)
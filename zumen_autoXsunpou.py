import FreeCAD as App
import FreeCADGui as Gui
import Draft
from PySide import QtWidgets, QtCore
import math


doc = App.ActiveDocument


# ============================================================
# レポートウィンドウ
# ============================================================

class XSunpouReportWindow(QtWidgets.QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "自動X寸法 - Draft"
        )

        self.resize(800, 650)

        layout = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel(
            "自動X寸法 - Draft寸法作成結果"
        )

        title.setAlignment(
            QtCore.Qt.AlignCenter
        )

        font = title.font()

        font.setPointSize(14)

        font.setBold(True)

        title.setFont(font)

        layout.addWidget(title)

        self.output = QtWidgets.QPlainTextEdit()

        self.output.setReadOnly(True)

        layout.addWidget(
            self.output
        )

        close_button = QtWidgets.QPushButton(
            "閉じる"
        )

        close_button.setMinimumHeight(
            40
        )

        layout.addWidget(
            close_button
        )

        close_button.clicked.connect(
            self.close
        )


    def println(self, text=""):

        text = str(text)

        print(text)

        self.output.appendPlainText(
            text
        )


# ============================================================
# 選択ライン取得
# ============================================================

def get_selected_line():

    selection = Gui.Selection.getSelectionEx()

    if not selection:

        return None

    for s in selection:

        obj = s.Object

        if obj is None:

            continue

        # ----------------------------------------------------
        # Draft Line
        # ----------------------------------------------------

        if (
            hasattr(obj, "Start")
            and hasattr(obj, "End")
        ):

            return obj

        # ----------------------------------------------------
        # ShapeからLine判定
        # ----------------------------------------------------

        try:

            if len(obj.Shape.Edges) == 1:

                edge = obj.Shape.Edges[0]

                curve = edge.Curve

                name = type(curve).__name__

                if (
                    name == "Line"
                    or "Line" in name
                ):

                    return obj

        except:

            pass

    return None


# ============================================================
# Layer検索
# ============================================================

def find_layer(target):

    if doc is None:

        return None

    # --------------------------------------------------------
    # 直接Group
    # --------------------------------------------------------

    for obj in doc.Objects:

        try:

            if not hasattr(
                obj,
                "Group"
            ):

                continue

            if target in list(
                obj.Group
            ):

                return obj

        except:

            pass

    # --------------------------------------------------------
    # 2階層
    # --------------------------------------------------------

    for obj in doc.Objects:

        try:

            if not hasattr(
                obj,
                "Group"
            ):

                continue

            for child in obj.Group:

                try:

                    if hasattr(
                        child,
                        "Group"
                    ):

                        if target in list(
                            child.Group
                        ):

                            return child

                except:

                    pass

        except:

            pass

    return None


# ============================================================
# Yプラス側の頂点を取得
# ============================================================

def get_y_plus_vertex(line):

    # --------------------------------------------------------
    # Draft Line の Start / End
    # --------------------------------------------------------

    try:

        p1 = line.Start

        p2 = line.End

        if p1.y >= p2.y:

            return p1

        else:

            return p2

    except:

        pass

    # --------------------------------------------------------
    # Shapeから取得
    # --------------------------------------------------------

    try:

        edge = line.Shape.Edges[0]

        vertices = edge.Vertexes

        if len(vertices) >= 2:

            p1 = vertices[0].Point

            p2 = vertices[-1].Point

            if p1.y >= p2.y:

                return p1

            else:

                return p2

    except:

        pass

    return None


# ============================================================
# X座標追加
# ============================================================

def add_x_point(
    points,
    x,
    source,
    obj
):

    try:

        x = float(x)

    except:

        return

    points.append({

        "x": x,

        "source": source,

        "name": obj.Name,

        "label": obj.Label

    })


# ============================================================
# Layer内のX座標を収集
#
# LINE
#     Start.X
#     End.X
#
# CIRCLE
#     Center.X
#
# ARC
#     Center.X
# ============================================================

def collect_x_points(layer):

    points = []

    try:

        objects = list(
            layer.Group
        )

    except:

        return points


    for obj in objects:

        try:

            if not hasattr(
                obj,
                "Shape"
            ):

                continue

            edges = obj.Shape.Edges

            if len(edges) != 1:

                continue

            edge = edges[0]

            curve = edge.Curve

            curve_name = (
                type(curve).__name__
            )


            # =================================================
            # LINE
            # =================================================

            if (
                curve_name == "Line"
                or "Line" in curve_name
            ):

                if len(
                    edge.Vertexes
                ) >= 2:

                    p1 = (
                        edge.Vertexes[0]
                        .Point
                    )

                    p2 = (
                        edge.Vertexes[-1]
                        .Point
                    )

                    add_x_point(
                        points,
                        p1.x,
                        "LINE Start",
                        obj
                    )

                    add_x_point(
                        points,
                        p2.x,
                        "LINE End",
                        obj
                    )

                continue


            # =================================================
            # CIRCLE / ARC
            # =================================================

            if (
                "Circle" in curve_name
                or "Arc" in curve_name
            ):

                try:

                    center = curve.Center

                    center_x = (
                        center.x
                    )

                except:

                    continue


                # ------------------------------------------------
                # 円 / 円弧判定
                # ------------------------------------------------

                is_arc = False

                try:

                    span = abs(
                        curve.LastParameter
                        -
                        curve.FirstParameter
                    )

                    if span < (
                        2.0 * math.pi
                        -
                        1e-7
                    ):

                        is_arc = True

                except:

                    pass


                if is_arc:

                    source = (
                        "ARC Center"
                    )

                else:

                    source = (
                        "CIRCLE Center"
                    )


                add_x_point(
                    points,
                    center_x,
                    source,
                    obj
                )

        except Exception as e:

            print(
                "X座標解析エラー:",
                getattr(
                    obj,
                    "Name",
                    "Unknown"
                ),
                e
            )

    return points


# ============================================================
# X座標重複除去
# ============================================================

def remove_duplicate_x(
    points,
    tolerance=1e-7
):

    result = []

    for p in points:

        duplicate = False

        for r in result:

            if abs(
                p["x"]
                -
                r["x"]
            ) <= tolerance:

                duplicate = True

                break

        if not duplicate:

            result.append(
                p
            )

    return result


# ============================================================
# 基準Xから近い順
# ============================================================

def sort_by_distance(
    points,
    base_x
):

    for p in points:

        p["distance"] = abs(
            p["x"]
            -
            base_x
        )

    points.sort(
        key=lambda p: (
            p["distance"],
            p["x"]
        )
    )

    return points


# ============================================================
# Draft X寸法作成
#
# p1 = 基準点
# p2 = 対象Xの点
# p3 = 寸法線位置
#
# WorkingPlaneは使用しない
# getViewDirectionも使用しない
# TechDrawも使用しない
# ============================================================

def create_x_dimension(
    base_point,
    target_x,
    dimension_y
):

    try:

        # ----------------------------------------------------
        # 基準点
        # ----------------------------------------------------

        p1 = App.Vector(
            base_point.x,
            base_point.y,
            base_point.z
        )

        # ----------------------------------------------------
        # 対象点
        #
        # Xだけ対象Xへ変更
        # ----------------------------------------------------

        p2 = App.Vector(
            target_x,
            base_point.y,
            base_point.z
        )

        # ----------------------------------------------------
        # 寸法線位置
        # ----------------------------------------------------

        p3 = App.Vector(
            (
                base_point.x
                +
                target_x
            ) / 2.0,
            dimension_y,
            base_point.z
        )

        # ----------------------------------------------------
        # Draft寸法作成
        # ----------------------------------------------------

        dimension = Draft.make_dimension(
            p1,
            p2,
            p3
        )

        if dimension is None:

            return None

        # ----------------------------------------------------
        # 寸法名
        # ----------------------------------------------------

        try:

            dimension.Label = (
                "X寸法"
            )

        except:

            pass

        return dimension

    except Exception as e:

        print(
            "寸法作成エラー:",
            e
        )

        return None


# ============================================================
# メイン
# ============================================================

def main():

    global doc

    doc = App.ActiveDocument

    if doc is None:

        QtWidgets.QMessageBox.warning(
            None,
            "自動X寸法",
            "アクティブなドキュメントがありません。"
        )

        return


    # ========================================================
    # 選択ライン
    # ========================================================

    line = get_selected_line()

    if line is None:

        QtWidgets.QMessageBox.warning(
            None,
            "自動X寸法",
            "Draftラインを1本選択してください。"
        )

        return


    # ========================================================
    # 基準点
    #
    # 選択ラインのYがプラス側の頂点
    # ========================================================

    base_point = (
        get_y_plus_vertex(line)
    )

    if base_point is None:

        QtWidgets.QMessageBox.critical(
            None,
            "自動X寸法",
            "基準ラインの頂点を取得できませんでした。"
        )

        return


    # ========================================================
    # 基準X
    # ========================================================

    base_x = float(
        base_point.x
    )

    base_y = float(
        base_point.y
    )


    # ========================================================
    # Layer
    # ========================================================

    layer = find_layer(
        line
    )

    if layer is None:

        QtWidgets.QMessageBox.warning(
            None,
            "自動X寸法",
            "選択ラインの所属Layerが見つかりません。"
        )

        return


    # ========================================================
    # レポートウィンドウ
    # ========================================================

    global x_report_window

    try:

        x_report_window.close()

    except:

        pass


    x_report_window = (
        XSunpouReportWindow()
    )

    x_report_window.setAttribute(
        QtCore.Qt.WA_DeleteOnClose,
        True
    )

    x_report_window.show()

    x_report_window.raise_()

    x_report_window.activateWindow()


    # ========================================================
    # レポート開始
    # ========================================================

    x_report_window.println(
        "============================================================"
    )

    x_report_window.println(
        "zumen_autoXsunpou.py"
    )

    x_report_window.println(
        "Draft自動X寸法"
    )

    x_report_window.println(
        "============================================================"
    )

    x_report_window.println("")

    x_report_window.println(
        "基準ライン = {}".format(
            line.Name
        )
    )

    x_report_window.println(
        "基準点 = Yプラス側頂点"
    )

    x_report_window.println(
        "基準X = {:.6f}".format(
            base_x
        )
    )

    x_report_window.println(
        "基準Y = {:.6f}".format(
            base_y
        )
    )

    x_report_window.println(
        "Layer = {}".format(
            layer.Label
        )
    )

    x_report_window.println("")


    # ========================================================
    # X座標収集
    # ========================================================

    points = collect_x_points(
        layer
    )


    # ========================================================
    # 基準Xと同じXを除外
    #
    # 基準点自身を寸法対象にしない
    # ========================================================

    filtered_points = []

    for p in points:

        if abs(
            p["x"]
            -
            base_x
        ) <= 1e-7:

            continue

        filtered_points.append(
            p
        )

    points = filtered_points


    # ========================================================
    # 重複除去
    # ========================================================

    points = remove_duplicate_x(
        points
    )


    # ========================================================
    # 基準Xから近い順
    # ========================================================

    points = sort_by_distance(
        points,
        base_x
    )


    # ========================================================
    # 寸法線の高さ
    #
    # 基準ラインのYより上に配置
    # ========================================================

    # モデルサイズに応じて10mm程度上へ
    dimension_offset = 10.0

    dimension_y = (
        base_y
        +
        dimension_offset
    )


    # ========================================================
    # 寸法作成
    # ========================================================

    created_count = 0


    x_report_window.println(
        "対象X座標数 = {}".format(
            len(points)
        )
    )

    x_report_window.println("")


    for i, p in enumerate(
        points,
        1
    ):

        variable_name = (
            "XVertex{}".format(i)
        )

        x_report_window.println(
            "{} = {:.6f}".format(
                variable_name,
                p["x"]
            )
        )


        # ----------------------------------------------------
        # 寸法作成
        # ----------------------------------------------------

        dimension = create_x_dimension(
            base_point,
            p["x"],
            dimension_y
        )


        if dimension is not None:

            created_count += 1


            # -----------------------------------------------
            # 作成された寸法をLayerへ追加
            # -----------------------------------------------

            try:

                group = list(
                    layer.Group
                )

                if dimension not in group:

                    group.append(
                        dimension
                    )

                    layer.Group = group

            except Exception as e:

                print(
                    "Layer追加エラー:",
                    e
                )


    # ========================================================
    # 再計算
    # ========================================================

    try:

        doc.recompute()

    except:

        pass


    # ========================================================
    # レポート終了
    # ========================================================

    x_report_window.println("")

    x_report_window.println(
        "============================================================"
    )

    x_report_window.println(
        "zumen_autoXsunpou.py"
    )

    x_report_window.println(
        "自動X寸法作成完了"
    )

    x_report_window.println(
        "============================================================"
    )

    x_report_window.println(
        "基準ライン = {}".format(
            line.Name
        )
    )

    x_report_window.println(
        "基準点 = Yプラス側頂点"
    )

    x_report_window.println(
        "基準X = {:.6f}".format(
            base_x
        )
    )

    x_report_window.println(
        "Layer = {}".format(
            layer.Label
        )
    )

    x_report_window.println(
        "対象X座標数 = {}".format(
            len(points)
        )
    )

    x_report_window.println(
        "作成寸法数 = {}".format(
            created_count
        )
    )

    x_report_window.println(
        "============================================================"
    )


# ============================================================
# 実行
# ============================================================

try:

    main()

except Exception as e:

    import traceback

    print(
        "zumen_autoXsunpou.py エラー:"
    )

    print(
        traceback.format_exc()
    )

    try:

        QtWidgets.QMessageBox.critical(
            None,
            "自動X寸法",
            "エラーが発生しました。\n\n{}".format(
                e
            )
        )

    except:

        pass
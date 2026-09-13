import FreeCAD as App
import FreeCADGui as Gui

from PySide import QtWidgets, QtCore

import math
import os

doc = App.ActiveDocument


class ZumenSupouWindow(QtWidgets.QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("寸法自動生成 - Draft解析")

        self.resize(800, 650)

        layout = QtWidgets.QVBoxLayout(self)

        # ========================================================
        # タイトル
        # ========================================================

        title = QtWidgets.QLabel("Draftライン・Layer解析")

        title.setAlignment(QtCore.Qt.AlignCenter)

        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)

        layout.addWidget(title)

        # ========================================================
        # 説明
        # ========================================================

        info = QtWidgets.QLabel(
            "Draftのラインを1本選択してから解析してください"
        )

        info.setAlignment(QtCore.Qt.AlignCenter)

        layout.addWidget(info)

        # ========================================================
        # 解析ボタン
        # ========================================================

        self.button = QtWidgets.QPushButton("選択ラインを解析")

        self.button.setMinimumHeight(45)

        layout.addWidget(self.button)

        # ========================================================
        # 自動X寸法ボタン
        # ========================================================

        self.x_dimension_button = QtWidgets.QPushButton("自動X寸法")

        self.x_dimension_button.setMinimumHeight(45)

        layout.addWidget(self.x_dimension_button)

        # ========================================================
        # 結果表示
        # ========================================================

        self.output = QtWidgets.QPlainTextEdit()

        self.output.setReadOnly(True)

        layout.addWidget(self.output)

        # ========================================================
        # 閉じるボタン
        # ========================================================

        self.close_button = QtWidgets.QPushButton("閉じる")

        layout.addWidget(self.close_button)

        # ========================================================
        # ボタン接続
        # ========================================================

        self.button.clicked.connect(self.analyze)

        self.x_dimension_button.clicked.connect(
            self.auto_x_dimension
        )

        self.close_button.clicked.connect(
            self.close
        )


    # ============================================================
    # 表示
    # ============================================================

    def println(self, text=""):

        text = str(text)

        print(text)

        self.output.appendPlainText(text)


    # ============================================================
    # 選択ライン取得
    # ============================================================

    def get_selected_object(self):

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

            if hasattr(obj, "Start") and hasattr(obj, "End"):

                return obj

            # ----------------------------------------------------
            # ShapeからLine判定
            # ----------------------------------------------------

            try:

                if len(obj.Shape.Edges) == 1:

                    edge = obj.Shape.Edges[0]

                    curve = edge.Curve

                    name = type(curve).__name__

                    if name == "Line" or "Line" in name:

                        return obj

            except:

                pass

        return None


    # ============================================================
    # Layer検索
    # ============================================================

    def find_layer(self, target):

        if doc is None:

            return None

        # --------------------------------------------------------
        # 直接Groupに入っている場合
        # --------------------------------------------------------

        for obj in doc.Objects:

            try:

                if not hasattr(obj, "Group"):

                    continue

                if target in list(obj.Group):

                    return obj

            except:

                pass

        # --------------------------------------------------------
        # 2階層まで検索
        # --------------------------------------------------------

        for obj in doc.Objects:

            try:

                if not hasattr(obj, "Group"):

                    continue

                for child in obj.Group:

                    try:

                        if hasattr(child, "Group"):

                            if target in list(child.Group):

                                return child

                    except:

                        pass

            except:

                pass

        return None


    # ============================================================
    # Layer情報
    # ============================================================

    def get_layer_info(self, layer):

        if layer is None:

            return None, 0

        try:

            objects = list(layer.Group)

            return layer.Label, len(objects)

        except:

            try:

                objects = list(layer.Group)

                return layer.Name, len(objects)

            except:

                return layer.Name, 0


    # ============================================================
    # 解析
    # ============================================================

    def analyze(self):

        self.output.clear()

        global doc

        doc = App.ActiveDocument

        if doc is None:

            self.println(
                "アクティブなドキュメントがありません。"
            )

            return

        # --------------------------------------------------------
        # 解析開始
        # --------------------------------------------------------

        self.println(
            "============================================================"
        )

        self.println(
            "zumensupou_main.py"
        )

        self.println(
            "解析開始"
        )

        self.println(
            "============================================================"
        )

        # --------------------------------------------------------
        # 選択ライン取得
        # --------------------------------------------------------

        obj = self.get_selected_object()

        if obj is None:

            self.println(
                "Draftラインが選択されていません。"
            )

            QtWidgets.QMessageBox.warning(
                self,
                "解析",
                "Draftラインを1本選択してください。"
            )

            return

        # --------------------------------------------------------
        # Layer取得
        # --------------------------------------------------------

        layer = self.find_layer(obj)

        if layer is None:

            self.println("")

            self.println(
                "【解析結果】"
            )

            self.println("")

            self.println(
                "所属Layerが見つかりません。"
            )

            self.println("")

            self.println(
                "==========="
            )

            self.println(
                "解析終了"
            )

            self.println(
                "==========="
            )

            return

        # --------------------------------------------------------
        # Layer名とオブジェクト数だけ取得
        # --------------------------------------------------------

        layer_name, object_count = self.get_layer_info(
            layer
        )

        # --------------------------------------------------------
        # 結果表示
        # --------------------------------------------------------

        self.println("")

        self.println(
            "【解析結果】"
        )

        self.println("")

        self.println(
            "Layer名 = {}".format(layer_name)
        )

        self.println(
            "オブジェクト数 = {}".format(object_count)
        )

        self.println("")

        self.println(
            "==========="
        )

        self.println(
            "解析終了"
        )

        self.println(
            "==========="
        )


    # ============================================================
    # 自動X寸法
    # ============================================================

    def auto_x_dimension(self):

        try:

            # ----------------------------------------------------
            # ユーザーマクロフォルダ
            # ----------------------------------------------------

            macro_dir = App.getUserMacroDir(True)

            # ----------------------------------------------------
            # マクロファイル
            # ----------------------------------------------------

            macro_path = os.path.join(
                macro_dir,
                "zumen_autoXsunpou.py"
            )

            print("")

            print(
                "============================================================"
            )

            print(
                "自動X寸法"
            )

            print(
                "============================================================"
            )

            print(
                "MacroDir = {}".format(
                    macro_dir
                )
            )

            print(
                "MacroPath = {}".format(
                    macro_path
                )
            )

            # ----------------------------------------------------
            # ファイル確認
            # ----------------------------------------------------

            if not os.path.isfile(macro_path):

                QtWidgets.QMessageBox.warning(
                    self,
                    "自動X寸法",
                    "zumen_autoXsunpou.py が見つかりません。\n\n{}".format(
                        macro_path
                    )
                )

                return

            # ----------------------------------------------------
            # マクロ読み込み
            # ----------------------------------------------------

            with open(
                macro_path,
                "r",
                encoding="utf-8"
            ) as f:

                code = f.read()

            # ----------------------------------------------------
            # マクロ実行
            # ----------------------------------------------------

            exec(
                compile(
                    code,
                    macro_path,
                    "exec"
                ),
                globals(),
                globals()
            )

            print(
                "zumen_autoXsunpou.py 実行完了"
            )

        except Exception as e:

            import traceback

            print("")

            print(
                "============================================================"
            )

            print(
                "zumen_autoXsunpou.py 起動エラー"
            )

            print(
                "============================================================"
            )

            print(
                traceback.format_exc()
            )

            QtWidgets.QMessageBox.critical(
                self,
                "自動X寸法",
                "zumen_autoXsunpou.py の実行中にエラーが発生しました。\n\n{}".format(
                    e
                )
            )


# ================================================================
# 起動
# ================================================================

try:

    window.close()

except:

    pass


window = ZumenSupouWindow()

window.setAttribute(
    QtCore.Qt.WA_DeleteOnClose,
    True
)

window.show()

window.raise_()

window.activateWindow()


print("")

print(
    "============================================================"
)

print(
    "zumensupou_main.py 起動"
)

print(
    "============================================================"
)

print(
    "Draftラインを1本選択してください"
)

print(
    "QTの「選択ラインを解析」を押してください"
)

print(
    "============================================================"
)
# ============================================================
# part_zumen_main.py
#
# 部品図作成メインスクリプト
#
# Qtウィジェット
#   ↓
# 回転角度入力
#   ↓
# 「5面生成」
#   ↓
# ① zumen5face.py
# ② zumen_lineexcenge.py
# ============================================================

import FreeCAD as App
import FreeCADGui as Gui
import os
import traceback

from PySide import QtWidgets, QtCore


# ============================================================
# FreeCADドキュメント
# ============================================================

doc = App.ActiveDocument

if doc is None:

    raise Exception(
        "FreeCADでドキュメントを開いてください"
    )


# ============================================================
# Mainスクリプトの場所
# ============================================================

MAIN_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# 使用するスクリプト
# ============================================================

ZUMEN5FACE = os.path.join(
    MAIN_DIR,
    "zumen5face.py"
)

ZUMEN_LINEEXCENGE = os.path.join(
    MAIN_DIR,
    "zumen_lineexcenge.py"
)


# ============================================================
# ファイル確認
# ============================================================

if not os.path.isfile(
    ZUMEN5FACE
):

    raise Exception(
        "zumen5face.py が見つかりません:\n"
        + ZUMEN5FACE
    )


if not os.path.isfile(
    ZUMEN_LINEEXCENGE
):

    raise Exception(
        "zumen_lineexcenge.py が見つかりません:\n"
        + ZUMEN_LINEEXCENGE
    )


# ============================================================
# スクリプト実行
#
# extra_globals:
#   別スクリプトへ値を渡すために使用
# ============================================================

def run_script(
    path,
    extra_globals=None
):

    print("")
    print("========================================")
    print("スクリプト実行")
    print("========================================")
    print(path)
    print("========================================")


    script_globals = {

        "__file__": path,

        "__name__": "__main__",

    }


    # --------------------------------------------------------
    # 外部から渡された値
    # --------------------------------------------------------

    if extra_globals:

        script_globals.update(
            extra_globals
        )


    # --------------------------------------------------------
    # ファイル読み込み
    # --------------------------------------------------------

    with open(
        path,
        "r",
        encoding="utf-8-sig"
    ) as f:

        code = f.read()


    # --------------------------------------------------------
    # 実行
    # --------------------------------------------------------

    exec(
        compile(
            code,
            path,
            "exec"
        ),
        script_globals
    )


    print("")
    print("========================================")
    print("スクリプト完了")
    print("========================================")


# ============================================================
# 5面生成
# ============================================================

def create_five_views():

    global doc


    # ========================================================
    # Face選択確認
    # ========================================================

    sel = Gui.Selection.getSelectionEx()

    if not sel:

        QtWidgets.QMessageBox.warning(

            window,

            "5面生成",

            "基準にするFaceを1枚選択してください。"

        )

        return


    # ========================================================
    # 回転角度取得
    # ========================================================

    rotation_angle = (
        window.angle_spin.value()
    )


    print("")
    print("========================================")
    print("部品図生成")
    print("========================================")

    print(
        "回転角度 =",
        rotation_angle,
        "deg"
    )


    # ========================================================
    # ① 5面投影
    # ========================================================

    print("")
    print("========================================")
    print("① zumen5face.py")
    print("========================================")


    try:

        run_script(
            ZUMEN5FACE
        )


    except Exception as e:

        print("")
        print("========================================")
        print("zumen5face.py エラー")
        print("========================================")

        traceback.print_exc()


        QtWidgets.QMessageBox.critical(

            window,

            "5面生成エラー",

            "zumen5face.py でエラーが発生しました。\n\n"
            + str(e)

        )

        return


    doc.recompute()


    # ========================================================
    # ② Draft Layer / Line化
    #
    # 回転角度を渡す
    # ========================================================

    print("")
    print("========================================")
    print("② zumen_lineexcenge.py")
    print("========================================")


    try:

        run_script(

            ZUMEN_LINEEXCENGE,

            {

                "ROTATION_ANGLE":
                    rotation_angle

            }

        )


    except Exception as e:

        print("")
        print("========================================")
        print("zumen_lineexcenge.py エラー")
        print("========================================")

        traceback.print_exc()


        QtWidgets.QMessageBox.critical(

            window,

            "5面生成エラー",

            "zumen_lineexcenge.py でエラーが発生しました。\n\n"
            + str(e)

        )

        return


    # ========================================================
    # 最終更新
    # ========================================================

    doc.recompute()

    Gui.activeDocument().activeView().fitAll()


    # ========================================================
    # 完了
    # ========================================================

    print("")
    print("========================================")
    print("5面生成完了")
    print("========================================")

    print(
        "回転角度 =",
        rotation_angle,
        "deg"
    )


    QtWidgets.QMessageBox.information(

        window,

        "5面生成",

        "5面生成が完了しました。\n\n"
        "回転角度 : %.1f°"
        % rotation_angle

    )


# ============================================================
# Qtウィンドウ
# ============================================================

class FiveViewWindow(
    QtWidgets.QWidget
):

    def __init__(self):

        super().__init__()


        # ====================================================
        # ウィンドウ
        # ====================================================

        self.setWindowTitle(
            "部品図作成"
        )

        self.setMinimumWidth(
            340
        )


        # ====================================================
        # ★ 配色
        #
        # 背景   → 濃い青
        # 文字   → 白
        # 入力欄 → 白背景・黒文字
        # ====================================================

        self.setStyleSheet("""

            QWidget {
                background-color: #17365D;
                color: white;
            }

            QLabel {
                color: white;
                background-color: transparent;
            }

            QPushButton {
                background-color: #2F75B5;
                color: white;
                border: 1px solid #5B9BD5;
                border-radius: 6px;
                padding: 8px;
            }

            QPushButton:hover {
                background-color: #3F86C6;
            }

            QPushButton:pressed {
                background-color: #1F5A8A;
            }

            QDoubleSpinBox {
                background-color: white;
                color: black;
                border: 1px solid #5B9BD5;
                border-radius: 4px;
                padding: 4px;
            }

            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button {
                background-color: #E6E6E6;
            }

            QMessageBox {
                background-color: #17365D;
                color: white;
            }

        """)


        # ====================================================
        # レイアウト
        # ====================================================

        layout = QtWidgets.QVBoxLayout(
            self
        )


        # ====================================================
        # タイトル
        # ====================================================

        title = QtWidgets.QLabel(
            "部品図作成"
        )

        title.setAlignment(
            QtCore.Qt.AlignCenter
        )


        font = title.font()

        font.setPointSize(
            14
        )

        font.setBold(
            True
        )

        title.setFont(
            font
        )


        layout.addWidget(
            title
        )


        # ====================================================
        # 説明
        # ====================================================

        info = QtWidgets.QLabel(

            "基準にするFaceを選択してから\n"
            "回転角度を指定して「5面生成」を押してください。"

        )

        info.setAlignment(
            QtCore.Qt.AlignCenter
        )


        layout.addWidget(
            info
        )


        # ====================================================
        # 回転角度
        # ====================================================

        angle_layout = QtWidgets.QHBoxLayout()


        angle_label = QtWidgets.QLabel(
            "回転角度"
        )


        self.angle_spin = (
            QtWidgets.QDoubleSpinBox()
        )


        self.angle_spin.setRange(
            -360.0,
            360.0
        )


        self.angle_spin.setDecimals(
            1
        )


        self.angle_spin.setSingleStep(
            15.0
        )


        self.angle_spin.setValue(
            90.0
        )


        self.angle_spin.setSuffix(
            " °"
        )


        angle_layout.addWidget(
            angle_label
        )

        angle_layout.addWidget(
            self.angle_spin
        )


        layout.addLayout(
            angle_layout
        )


        # ====================================================
        # 5面生成ボタン
        # ====================================================

        self.create_button = (
            QtWidgets.QPushButton(
                "5面生成"
            )
        )


        self.create_button.setMinimumHeight(
            50
        )


        button_font = (
            self.create_button.font()
        )


        button_font.setPointSize(
            12
        )


        button_font.setBold(
            True
        )


        self.create_button.setFont(
            button_font
        )


        layout.addWidget(
            self.create_button
        )


        # ====================================================
        # 閉じる
        # ====================================================

        self.close_button = (
            QtWidgets.QPushButton(
                "閉じる"
            )
        )


        layout.addWidget(
            self.close_button
        )


        # ====================================================
        # シグナル
        # ====================================================

        self.create_button.clicked.connect(
            create_five_views
        )

        self.close_button.clicked.connect(
            self.close
        )


# ============================================================
# ウィンドウ表示
# ============================================================

window = FiveViewWindow()


window.setAttribute(
    QtCore.Qt.WA_DeleteOnClose,
    True
)


window.show()

window.raise_()

window.activateWindow()


# ============================================================
# 起動メッセージ
# ============================================================

print("")
print("========================================")
print("部品図作成ウィジェット起動")
print("========================================")
print("基準Faceを選択してください")
print("回転角度を指定してください")
print("「5面生成」を押すと処理開始")
print("========================================")
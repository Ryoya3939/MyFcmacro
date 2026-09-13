
import FreeCAD as App
import FreeCADGui as Gui
import Draft

from PySide import QtCore
from PySide import QtWidgets


class CenterLineWidget(QtWidgets.QDialog):

    def __init__(self):

        super(CenterLineWidget, self).__init__(None)

        self.setWindowTitle(
            "OBJ中心に十字中心線を作成・原点移動"
        )

        self.resize(
            360,
            250
        )

        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Window
        )

        self.setAttribute(
            QtCore.Qt.WA_DeleteOnClose,
            True
        )

        self.setup_ui()


    def setup_ui(self):

        layout = QtWidgets.QVBoxLayout(
            self
        )


        title = QtWidgets.QLabel(
            "OBJ中心に十字中心線を作成"
        )

        title.setAlignment(
            QtCore.Qt.AlignCenter
        )

        title.setStyleSheet(
            "font-weight: bold;"
        )

        layout.addWidget(
            title
        )


        info = QtWidgets.QLabel(
            "① グループを作成\n"
            "② 中心線を作成\n"
            "③ OBJ＋中心線を原点へ移動\n"
            "④ 最後にグループへまとめる"
        )

        info.setAlignment(
            QtCore.Qt.AlignCenter
        )

        layout.addWidget(
            info
        )


        button = QtWidgets.QPushButton(
            "中心線を作成して原点へ移動"
        )

        button.setMinimumHeight(
            45
        )

        button.setStyleSheet(
            "QPushButton {"
            "background-color: #2b579a;"
            "color: white;"
            "font-weight: bold;"
            "}"
        )

        button.clicked.connect(
            self.create_center_lines
        )

        layout.addWidget(
            button
        )


        close_button = QtWidgets.QPushButton(
            "閉じる"
        )

        close_button.clicked.connect(
            self.close
        )

        layout.addWidget(
            close_button
        )


        self.status = QtWidgets.QLabel(
            "OBJを選択してください"
        )

        self.status.setAlignment(
            QtCore.Qt.AlignCenter
        )

        self.status.setStyleSheet(
            "color: gray;"
        )

        layout.addWidget(
            self.status
        )


    def get_selected_center_and_size(self):

        selection = (
            Gui.Selection.getSelection()
        )

        if not selection:

            return None


        boxes = []


        for obj in selection:

            try:

                if hasattr(
                    obj,
                    "Shape"
                ):

                    if not obj.Shape.isNull():

                        boxes.append(
                            obj.Shape.BoundBox
                        )

            except Exception:

                pass


        if not boxes:

            return None


        xmin = min(
            box.XMin
            for box in boxes
        )

        xmax = max(
            box.XMax
            for box in boxes
        )

        ymin = min(
            box.YMin
            for box in boxes
        )

        ymax = max(
            box.YMax
            for box in boxes
        )

        zmin = min(
            box.ZMin
            for box in boxes
        )

        zmax = max(
            box.ZMax
            for box in boxes
        )


        center = App.Vector(
            (xmin + xmax) / 2.0,
            (ymin + ymax) / 2.0,
            (zmin + zmax) / 2.0
        )


        size_x = xmax - xmin

        size_y = ymax - ymin


        return (
            center,
            size_x,
            size_y
        )


    def create_center_lines(self):

        doc = App.ActiveDocument

        if doc is None:

            return


        # ====================================================
        # ① 最初に選択OBJを取得
        # ====================================================

        selection = (
            Gui.Selection.getSelection()
        )


        if not selection:

            QtWidgets.QMessageBox.warning(
                self,
                "選択なし",
                "OBJを選択してください。"
            )

            return


        # ====================================================
        # ② 最初に空の新規グループを作成
        #
        # この時点では何も入れない
        # ====================================================

        group = doc.addObject(
            "App::DocumentObjectGroup",
            "OBJ_Center_Group"
        )

        group.Label = (
            "OBJ中心・原点移動"
        )


        # ====================================================
        # ③ OBJの中心と大きさを取得
        # ====================================================

        result = (
            self.get_selected_center_and_size()
        )


        if result is None:

            try:

                doc.removeObject(
                    group.Name
                )

            except Exception:

                pass


            QtWidgets.QMessageBox.warning(
                self,
                "中心取得エラー",
                "OBJの中心を取得できませんでした。\n"
                "処理を中止しました。"
            )

            return


        center = result[0]

        size_x = result[1]

        size_y = result[2]


        # ====================================================
        # ④ 十字線の長さ
        # ====================================================

        half_length = (
            max(
                size_x,
                size_y
            ) / 2.0
            + 10.0
        )


        if half_length < 10.0:

            half_length = 10.0


        # ====================================================
        # ⑤ X方向中心線
        # ====================================================

        x_start = App.Vector(
            center.x - half_length,
            center.y,
            center.z
        )

        x_end = App.Vector(
            center.x + half_length,
            center.y,
            center.z
        )


        # ====================================================
        # ⑥ Y方向中心線
        # ====================================================

        y_start = App.Vector(
            center.x,
            center.y - half_length,
            center.z
        )

        y_end = App.Vector(
            center.x,
            center.y + half_length,
            center.z
        )


        # ====================================================
        # ⑦ 十字線を作成
        # ====================================================

        x_line = Draft.make_wire(
            [
                x_start,
                x_end
            ],
            closed=False
        )


        y_line = Draft.make_wire(
            [
                y_start,
                y_end
            ],
            closed=False
        )


        # ====================================================
        # ⑧ 一点鎖線に設定
        # ====================================================

        center_lines = [
            x_line,
            y_line
        ]


        for obj in center_lines:

            try:

                obj.ViewObject.LineWidth = 1.0

            except Exception:

                pass


            try:

                obj.ViewObject.LineColor = (
                    0.0,
                    0.0,
                    1.0,
                    1.0
                )

            except Exception:

                pass


            try:

                obj.ViewObject.DrawStyle = (
                    "Dashdot"
                )

            except Exception:

                pass


        doc.recompute()


        # ====================================================
        # ⑨ 中心線作成成功
        #
        # ここから原点移動
        # ====================================================

        move_vector = App.Vector(
            -center.x,
            -center.y,
            -center.z
        )


        # ====================================================
        # ⑩ OBJ＋中心線を移動対象にする
        # ====================================================

        move_objects = list(
            selection
        )


        move_objects.append(
            x_line
        )

        move_objects.append(
            y_line
        )


        # ====================================================
        # ⑪ OBJ＋中心線を原点へ移動
        # ====================================================

        doc.openTransaction(
            "中心線作成後に原点移動"
        )


        moved_count = 0


        for obj in move_objects:

            try:

                if hasattr(
                    obj,
                    "Placement"
                ):

                    obj.Placement.Base = (
                        obj.Placement.Base
                        + move_vector
                    )

                    moved_count += 1

            except Exception:

                pass


        doc.recompute()

        doc.commitTransaction()


        # ====================================================
        # ⑫ 最後に全部をグループへ入れる
        #
        # ここで初めてグループへ追加
        # ====================================================

        for obj in move_objects:

            try:

                if obj is not group:

                    group.addObject(
                        obj
                    )

            except Exception:

                pass


        doc.recompute()


        # ====================================================
        # ⑬ 表示更新
        # ====================================================

        self.status.setText(
            "完了\n"
            "中心線作成 → 原点移動 → グループ化\n"
            "中心 = (0.000, 0.000, 0.000)"
        )

        self.status.setStyleSheet(
            "color: green;"
            "font-weight: bold;"
        )


        Gui.updateGui()


        QtWidgets.QMessageBox.information(
            self,
            "完了",
            "処理が完了しました。\n\n"
            "① 新規グループ作成\n"
            "② 十字中心線作成\n"
            "③ OBJ＋中心線を原点へ移動\n"
            "④ 最後にグループへ追加\n\n"
            "移動数：{}個".format(
                moved_count
            )
        )


    def closeEvent(self, event):

        event.accept()


if "center_line_widget" in globals():

    try:

        center_line_widget.close()

    except Exception:

        pass


center_line_widget = CenterLineWidget()

center_line_widget.show()

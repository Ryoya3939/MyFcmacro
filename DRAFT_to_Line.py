import FreeCAD as App
import FreeCADGui as Gui
import Draft


doc = App.ActiveDocument


# ============================================================
# 処理結果グループ作成
# ============================================================

GROUP_NAME = "Downgrade_Results"

result_group = doc.getObject(GROUP_NAME)

if result_group is None:

    result_group = doc.addObject(
        "App::DocumentObjectGroup",
        GROUP_NAME
    )

    result_group.Label = "Downgrade Results"


# ============================================================
# 選択取得
# ============================================================

selection = Gui.Selection.getSelection()

if not selection:
    raise Exception("オブジェクトを選択してください。")


# ============================================================
# Edge単体かどうか判定
# ============================================================

def is_edge_object(obj):

    if not hasattr(obj, "Shape"):
        return False

    try:
        return len(obj.Shape.Edges) == 1
    except:
        return False


# ============================================================
# ダウングレード対象か判定
#
# Line / Wireのみ
# ============================================================

def is_downgrade_target(obj):

    # Edge単体は除外
    if is_edge_object(obj):
        return False

    if not hasattr(obj, "Shape"):
        return False

    try:

        # 複数のEdgeを持つものはWireとして処理
        if len(obj.Shape.Edges) > 1:
            return True

    except:
        pass


    # 名前・TypeIdからLine / Wireを判定
    text = (
        str(getattr(obj, "TypeId", "")) + " " +
        str(getattr(obj, "Name", "")) + " " +
        str(getattr(obj, "Label", ""))
    ).lower()


    if "line" in text:
        return True

    if "wire" in text:
        return True

    return False


# ============================================================
# 初期処理
# ============================================================

current_objects = []
final_objects = []


for obj in selection:

    # Edge単体はダウングレードせず最終解析へ
    if is_edge_object(obj):

        App.Console.PrintMessage(
            f"Edge - ダウングレード除外: {obj.Name}\n"
        )

        final_objects.append(obj)
        continue


    # Line / Wireはダウングレード対象
    if is_downgrade_target(obj):

        App.Console.PrintMessage(
            f"ダウングレード対象: {obj.Name}\n"
        )

        current_objects.append(obj)
        continue


    App.Console.PrintMessage(
        f"対象外: {obj.Name}\n"
    )


# ============================================================
# ダウングレード対象がなくなるまで繰り返す
# ============================================================

iteration = 0


while current_objects:

    iteration += 1

    App.Console.PrintMessage(
        f"\n--- ダウングレード {iteration} 回目 ---\n"
    )


    next_objects = []


    # ========================================================
    # 現在の対象を順番に処理
    # ========================================================

    for obj in current_objects:

        try:
            obj_name = obj.Name
        except:
            continue


        # ----------------------------------------------------
        # ダウングレード前のオブジェクト一覧
        # ----------------------------------------------------

        before_names = set(
            document_obj.Name
            for document_obj in doc.Objects
        )


        # ----------------------------------------------------
        # ダウングレード実行
        # ----------------------------------------------------

        try:

            Draft.downgrade(obj)
            doc.recompute()

        except Exception:

            App.Console.PrintMessage(
                f"ダウングレード失敗: {obj_name}\n"
            )

            final_objects.append(obj)

            continue


        # ----------------------------------------------------
        # 新しく作られたオブジェクトを取得
        # ----------------------------------------------------

        created_objects = []


        for document_obj in doc.Objects:

            if document_obj.Name not in before_names:

                # グループ自体は除外
                if document_obj.Name == GROUP_NAME:
                    continue

                created_objects.append(document_obj)


        # ----------------------------------------------------
        # ダウングレード不可
        # ----------------------------------------------------

        if not created_objects:

            App.Console.PrintMessage(
                f"ダウングレード不可: {obj_name}\n"
            )

            final_objects.append(obj)

            continue


        # ----------------------------------------------------
        # 新しく作られたものを結果グループへ追加
        # ----------------------------------------------------

        for new_obj in created_objects:

            try:

                result_group.addObject(new_obj)

            except Exception as e:

                App.Console.PrintMessage(
                    f"グループ追加エラー: {e}\n"
                )


        # ----------------------------------------------------
        # 新しくできたものを分類
        # ----------------------------------------------------

        for new_obj in created_objects:

            try:
                new_name = new_obj.Name
            except:
                continue


            # Edge単体なら最終解析へ
            if is_edge_object(new_obj):

                App.Console.PrintMessage(
                    f"Edge - 最終解析へ: {new_name}\n"
                )

                final_objects.append(new_obj)

                continue


            # Line / Wireなら次のダウングレードへ
            if is_downgrade_target(new_obj):

                App.Console.PrintMessage(
                    f"次のダウングレード対象: {new_name}\n"
                )

                next_objects.append(new_obj)

                continue


            # その他は最終解析へ
            final_objects.append(new_obj)


    # ========================================================
    # 次の対象へ
    # ========================================================

    current_objects = next_objects


# ============================================================
# 重複オブジェクトを削除
# ============================================================

unique_objects = []
seen_names = set()


for obj in final_objects:

    try:

        if obj.Name in seen_names:
            continue

        seen_names.add(obj.Name)

        unique_objects.append(obj)

    except:
        continue


# ============================================================
# 最終解析
#
# 直線Edge → Draft Line
# ============================================================

line_count = 0
processed_edges = set()


for obj in unique_objects:

    if not hasattr(obj, "Shape"):
        continue


    try:
        edges = obj.Shape.Edges
    except:
        continue


    for edge in edges:

        try:

            # 直線以外はスキップ
            if edge.Curve.TypeId != "Part::GeomLine":
                continue

            if len(edge.Vertexes) < 2:
                continue


            start = edge.Vertexes[0].Point
            end = edge.Vertexes[-1].Point


            # ------------------------------------------------
            # 重複線判定
            # ------------------------------------------------

            key = (
                round(start.x, 6),
                round(start.y, 6),
                round(start.z, 6),
                round(end.x, 6),
                round(end.y, 6),
                round(end.z, 6)
            )

            reverse_key = (
                round(end.x, 6),
                round(end.y, 6),
                round(end.z, 6),
                round(start.x, 6),
                round(start.y, 6),
                round(start.z, 6)
            )


            if key in processed_edges:
                continue

            if reverse_key in processed_edges:
                continue


            processed_edges.add(key)


            # ------------------------------------------------
            # Draft Line作成
            # ------------------------------------------------

            new_line = Draft.make_line(
                start,
                end
            )


            # ------------------------------------------------
            # 作成したDraft Lineを結果グループへ追加
            # ------------------------------------------------

            try:

                result_group.addObject(new_line)

            except Exception as e:

                App.Console.PrintMessage(
                    f"Lineグループ追加エラー: {e}\n"
                )


            line_count += 1


        except Exception as e:

            App.Console.PrintMessage(
                f"Edge処理エラー: {e}\n"
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
    f"完了: {line_count} 本のDraft Lineを作成しました。\n"
)

App.Console.PrintMessage(
    "========================================\n"
)# ============================================================
# Downgrade Results グループ内のEdgeを
# 1個ずつアップグレード
#
# アップグレード成功後、元のEdgeを削除
# ============================================================

App.Console.PrintMessage(
    "\n========================================\n"
)

App.Console.PrintMessage(
    "Edgeアップグレード開始\n"
)

App.Console.PrintMessage(
    "========================================\n"
)


# グループを再取得
result_group = doc.getObject("Downgrade_Results")

if result_group is None:

    raise Exception(
        "Downgrade Results グループが見つかりません。"
    )


# ------------------------------------------------------------
# 処理対象を先に取得
#
# 途中で削除するため、Groupを直接ループしない
# ------------------------------------------------------------

upgrade_targets = []


for obj in list(result_group.Group):

    try:

        # Shapeを持たないものは除外
        if not hasattr(obj, "Shape"):
            continue


        # Edgeが1本だけのものを対象
        if len(obj.Shape.Edges) != 1:
            continue


        upgrade_targets.append(obj)

    except:
        continue


# ------------------------------------------------------------
# 1個ずつアップグレード
# ------------------------------------------------------------

upgrade_count = 0


for obj in upgrade_targets:

    try:

        obj_name = obj.Name

    except:

        continue


    App.Console.PrintMessage(
        f"\nアップグレード: {obj_name}\n"
    )


    # --------------------------------------------------------
    # アップグレード前のオブジェクト一覧
    # --------------------------------------------------------

    before_names = set(
        document_obj.Name
        for document_obj in doc.Objects
    )


    # --------------------------------------------------------
    # アップグレード実行
    # --------------------------------------------------------

    try:

        Draft.upgrade(obj)

        doc.recompute()


    except Exception as e:

        App.Console.PrintMessage(
            f"アップグレード失敗: {obj_name} : {e}\n"
        )

        continue


    # --------------------------------------------------------
    # 新しく作られたオブジェクトを取得
    # --------------------------------------------------------

    created_objects = []


    for document_obj in doc.Objects:

        if document_obj.Name not in before_names:

            # グループ自身は除外
            if document_obj.Name == result_group.Name:
                continue

            created_objects.append(document_obj)


    # --------------------------------------------------------
    # 新しいオブジェクトができたか確認
    # --------------------------------------------------------

    if not created_objects:

        App.Console.PrintMessage(
            f"アップグレード不可: {obj_name}\n"
        )

        continue


    # --------------------------------------------------------
    # 新しく作られたものをグループへ追加
    # --------------------------------------------------------

    for new_obj in created_objects:

        try:

            result_group.addObject(new_obj)

            App.Console.PrintMessage(
                f"アップグレード結果を追加: {new_obj.Name}\n"
            )

        except Exception as e:

            App.Console.PrintMessage(
                f"グループ追加エラー: {e}\n"
            )


    # --------------------------------------------------------
    # アップグレード成功
    #
    # 元のEdgeを削除
    # --------------------------------------------------------

    try:

        # 先にグループから外す
        result_group.removeObject(obj)

        # ドキュメントから削除
        doc.removeObject(obj.Name)

        doc.recompute()

        App.Console.PrintMessage(
            f"元Edgeを削除: {obj_name}\n"
        )

        upgrade_count += 1


    except Exception as e:

        App.Console.PrintMessage(
            f"元Edge削除エラー: {obj_name} : {e}\n"
        )


# ============================================================
# 完了
# ============================================================

doc.recompute()


App.Console.PrintMessage(
    "\n========================================\n"
)

App.Console.PrintMessage(
    f"アップグレード完了: {upgrade_count} 個\n"
)

App.Console.PrintMessage(
    "========================================\n"
)
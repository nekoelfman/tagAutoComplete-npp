# -*- coding: utf-8 -*-

import re
from Npp import editor, console

# ----------------------------------------------------------------------------------------
# 説明
#   指定したタグ(選択範囲or現在のカーソル位置の語)の重みを調整する
#   いわゆる(word:1.1)とか(negative:-1)みたいな重み付けをキー入力で調整するスクリプト
#   incrementWordStrengthとdecrementWordStrengthをそれぞれNotepad++のショートカットキーに登録してご利用ください
#
# ----------------------------------------------------------------------------------------
# 設定項目
#   以下の変数の値を変更する事で設定を変更できます
#   NUM_STEP: 数値を増減させる量
NUM_STEP = 0.1

#     pattern = r'\(.+:-?\d+\.?\d*\)'
def search_pattern_from_text(pattern, text, start_pos, end_pos):
    for match in re.finditer(pattern, text):
        match_start_pos = match.start()
        match_end_pos = match.end()
        # マッチした部分が対象範囲内の位置かどうかを確認
        if match_start_pos <= start_pos and match_end_pos >= end_pos:
            search_pattern_from_text(pattern, match.group(), start_pos - match_start_pos, end_pos - match_start_pos)

        if (line_start_pos + match_start_pos) <= target_start_pos and (line_start_pos + match_end_pos) >= target_end_pos:
            console.write("Match: {}:{}\n".format(match.group(1), match.group(2)))
            target_word = match.group(1)
            try:
                weight_val = float(match.group(2)) # 正規表現にマッチした数値を小数に変換
            except ValueError:
                return
            start_pos = line_start_pos + match_start_pos
            end_pos = line_start_pos + match_end_pos
            break

# ----------------------------------------------------------------------------------------
# カーソル位置の語or選択範囲の重みを増減する
#   isIncrease: TrueでNUM_STEP分増加、FalseでNUM_STEP分減少
def process_word_at_cursor(isIncrease):

    selection_start = editor.getSelectionStart()
    selection_end = editor.getSelectionEnd()
    current_pos = editor.getCurrentPos()

    if selection_start == selection_end: # テキストが選択されていない時の位置取得
        current_word = editor.getWord(current_pos, True)
        target_start_pos = editor.wordStartPosition(current_pos, True)
        target_end_pos = editor.wordEndPosition(current_pos, True)
    else: # テキストが選択されている時の位置取得
        current_word = editor.getSelText()
        target_start_pos = selection_start
        target_end_pos = selection_end

    if target_start_pos == target_end_pos:
        return

    start_pos = -1
    end_pos = -1
    cursor_offset = 0

    # --- 数値付き括弧の中にある語かどうか確認 ---

    current_line_num = editor.lineFromPosition(current_pos)
    line_start_pos = editor.positionFromLine(current_line_num) # 最大探索範囲の先頭位置
    line_end_pos = editor.getLineEndPosition(current_line_num) # 最大探索範囲の末端位置
    current_line_text = editor.getTextRange(line_start_pos, line_end_pos)

    # (word:[-]num)の形式で現在の行のテキストを検索
    pattern = r'\((.+):(-?\d+\.?\d*)\)'
    for match in re.finditer(pattern, current_line_text):
        match_start_pos = match.start()
        match_end_pos = match.end()
        # マッチした部分が現在の選択位置かどうかを確認
        if (line_start_pos + match_start_pos) <= target_start_pos and (line_start_pos + match_end_pos) >= target_end_pos:
            console.write("Match: {}:{}\n".format(match.group(1), match.group(2)))
            target_word = match.group(1)
            try:
                weight_val = float(match.group(2)) # 正規表現にマッチした数値を小数に変換
            except ValueError:
                return
            start_pos = line_start_pos + match_start_pos
            end_pos = line_start_pos + match_end_pos
            break

    # 数値付き括弧の中に無い場合
    if start_pos == -1:
        start_pos = target_start_pos
        end_pos = target_end_pos
        target_word = current_word
        weight_val = 1.0
        cursor_offset = 1


    # --- 範囲内のテキストの重み(数値)を調整する ---

    if not target_word:
        return

    if isIncrease:
        weight_val += NUM_STEP
    else:
        weight_val -= NUM_STEP


    # --- 選択された元のテキストを、加工後のテキストで置き換える ---
    output_text = '({}:{})'.format(target_word, weight_val)
    editor.setTargetRange(start_pos, end_pos)
    editor.replaceTarget(output_text)

    # カーソル位置を移動
    editor.gotoPos(current_pos + cursor_offset)

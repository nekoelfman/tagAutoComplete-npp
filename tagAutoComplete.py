# -*- coding: utf-8 -*-
# Notepad++ Python Script for tag auto-completion.

import os
import csv

# ----------------------------------------------------------------------------------------
# 説明
#   A1111やComfyUIでおなじみのTag Auto CompleteをNotepad++で実装しました
#   LoadTextノード等と合わせてご利用ください
#   Python Script plugin for Notepad++[https://github.com/bruderstein/PythonScript]を利用します
#     [プラグイン] -> [プラグイン管理] から [PythonScript]プラグインをインストールしてください
#     PythonScriptのバージョン2.1で動作を確認しています
#   スクリプトと同じフォルダにあるファイルからタグ一覧を取得します
#     CSVファイルの各行の一列目の値をタグとして扱います
#     CSVファイルの一行目にヘッダー行がある場合は削除してください
#   スペースを含むタグを補完する時はスペースをアンダーバーに置き換えて入力してください
#     例: flat chest -> flat_chest
#
# 注意点
#   設定を変更したりスクリプト自体を終了する場合は一旦Notepad++を終了させてください
#   挙動がおかしい時は [プラグイン] -> [Python Script] -> [Show Console] の出力を確認してください
#     AutoComplete ENABLED for file: ... が表示されていない場合は有効化されていません
#   部分一致は不安定です。誰か原因を教えて...

# ----------------------------------------------------------------------------------------
# 設定項目
#   以下の変数の値を変更する事で設定を変更できます
#   TARGET_FILENAME: 対象のファイル名を指定する
#     - フルパスではなくファイル名
#     - '.txt'のように拡張子で有効化するファイル名を指定できます
#       (ファイル名の末尾で判断しています。ワイルドカード等は不可)
#   TAG_FILENAME: 入力補完に使用するタグ一覧のファイル名を指定する
#     - ファイルはこのスクリプトと同じフォルダに入れてください
#     - リストの上から順番に表示します
#   NUM_SHOW: 入力候補を表示するまでに必要な文字数
#   MAX_SHOW_WORDS: メニューに表示する候補の最大値
#   REPLACE_UB_TO_SPACE: アンダーバーをスペースに置換する
#   TEXT_SEPARATER: タグの末尾に付ける区切り文字
#   OPT_WORD_IN: タグ検索時の設定
#     - True: 部分一致(例: behindと入力した時にfrom_behindが候補に出る)
#     - False: 前方一致(例: behindと入力した時にfrom_behindは出ない)

TARGET_FILENAME = '.txt'
TAG_FILENAME = 'danbooru.csv'
NUM_SHOW = 2
MAX_SHOW_WORDS = 7
REPLACE_UB_TO_SPACE = True
TEXT_SEPARATER = ', '
OPT_WORD_IN = False

tags = []

# ----------------------------------------------------------------------------------------
# ファイルからタグ一覧を読み込む
def load_words_from_csv(filepath):
    """
    指定されたパスのCSVファイルを読み込み、各行の最初の列から単語のリストを返す。
    """

    words = []
    try:
        with open(filepath, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                # 行が空でなく、かつ最初の列に値がある場合のみ処理
                if row and row[0].strip():
                    # UTF-8にデコードしてPythonのユニコード文字列として扱う
                    word = row[0].strip().decode('utf-8')
                    words.append(word)
        
        console.write("Successfully loaded {} words from {}\n".format(len(words), os.path.basename(filepath)))
    
    except IOError:
        # ファイルが存在しない場合は、コンソールにメッセージを表示するだけ
        console.write("Info: {} not found. Skipping.\n".format(os.path.basename(filepath)))
        console.write("タグ補完に使用するファイルが無い\n")
        exit
    except Exception as e:
        # その他のエラーが発生した場合
        console.write("Error reading {}: {}\n".format(os.path.basename(filepath), e))
        console.write("タグ補完に使用するファイルが読み込めなかった\n")
        exit

    return words


# ----------------------------------------------------------------------------------------
# 文字入力時の補完処理
def on_char_added(args):
    current_pos = editor.getCurrentPos()
    current_word = editor.getWord(current_pos, True)
    
    if len(current_word) < NUM_SHOW:
        return

    suggestions = []
    for word in tags:
        if len(suggestions) >= MAX_SHOW_WORDS:
            break

        if OPT_WORD_IN: # 部分一致
            if current_word.lower() in word.lower():
                suggestions.append(word)
        else: # 前方一致
            if word.lower().startswith(current_word.lower()):
                suggestions.append(word)

    # 候補が存在する時にメニューを表示
    if suggestions:
        # 現在のセパレーターの設定を取得する
        current_sep = editor.autoCGetSeparator()
        # リストのセパレーターを','(Ascii:44)に変更する
        editor.autoCSetSeparator(44)
        editor.autoCShow(len(current_word), ",".join(suggestions))
        # セパレーターを元の設定に戻す
        editor.autoCSetSeparator(current_sep)


# ----------------------------------------------------------------------------------------
# オートコンプリート項目選択後の加工処理
def on_autocompletion_selected(args):
    """
    Called after an item from the auto-completion list is selected.
    'args['text']' contains the selected word.
    """

    selected_text = args['text']
    current_pos = editor.getCurrentPos()
    replace_start_pos = current_pos - len(selected_text) # テキスト置換の開始位置

    output_text = selected_text

    # アンダーバーをスペースに置換
    if REPLACE_UB_TO_SPACE:
        output_text = output_text.replace('_',' ')

    # 末尾に区切り文字を付ける
    output_text = output_text + TEXT_SEPARATER

    cursor_offset = len(output_text) # 最終的にカーソルを移動する位置

    if selected_text == output_text:
        return # 加工する必要無し

    # 選択された元のテキストを、加工後のテキストで置き換える
    editor.setTargetRange(replace_start_pos, current_pos)
    editor.replaceTarget(output_text)
    
    # カーソル位置を計算して移動
    final_cursor_pos = replace_start_pos + cursor_offset
    editor.gotoPos(final_cursor_pos)



# ----------------------------------------------------------------------------------------
# ファイル（バッファ）が切り替わった時の処理
def on_buffer_activated(args):

    # バッファが切り替わった時は(二重に登録されてしまうため事を防ぐため)一旦コールバックを解除する
    editor.clearCallbacks([SCINTILLANOTIFICATION.CHARADDED, SCINTILLANOTIFICATION.AUTOCSELECTION])

    # 特定のファイル名、または特定の拡張子で判定
    current_filename = notepad.getCurrentFilename()
    if current_filename.endswith(TARGET_FILENAME):
        # 対象ファイルなら、コールバックを登録
        editor.callback(on_char_added, [SCINTILLANOTIFICATION.CHARADDED])
        editor.callback(on_autocompletion_selected, [SCINTILLANOTIFICATION.AUTOCSELECTION])
        console.write("AutoComplete ENABLED for file: {}\n".format(current_filename))


# ----------------------------------------------------------------------------------------
# スクリプトの初期化

# スクリプト自身のパスを取得して、CSVファイルのフルパスを構築
script_dir = os.path.dirname(__file__.decode('utf-8')) # パスが非ASCII文字を含む場合に備える
csv_filepath = os.path.join(script_dir, TAG_FILENAME)

# CSVファイルから単語を読み込む
tags = load_words_from_csv(csv_filepath)
if len(tags):
    # BUFFERACTIVATED イベントが発生するたびに on_buffer_activated を呼び出すよう登録
    notepad.callback(on_buffer_activated, [NOTIFICATION.BUFFERACTIVATED])
    # スクリプト実行時に、現在開いているファイルに対して一度チェックを実行
    on_buffer_activated(None) 

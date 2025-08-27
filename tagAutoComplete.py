# -*- coding: utf-8 -*-
# Notepad++ Python Script for tag auto-completion.

import os
import csv
from Npp import editor, notepad, console, SCINTILLANOTIFICATION, NOTIFICATION

# ----------------------------------------------------------------------------------------
# 説明
#   A1111やComfyUIでおなじみのTag Auto CompleteのNotepad++での実装を目指しています
#   ComfyUIのLoadTextノード等と合わせてご利用ください
#   Python Script plugin for Notepad++[https://github.com/bruderstein/PythonScript]を利用します
#     [プラグイン] -> [プラグイン管理] から [PythonScript]プラグインをインストールしてください
#     PythonScriptのバージョン2.1で動作を確認しています
#   スクリプトと同じフォルダにあるファイルからタグ一覧を取得します
#     CSVファイルの各行の一列目の値をタグとして扱います
#     CSVファイルの一行目にヘッダー行がある場合は削除してください
#   スペースを含むタグを補完する時はスペースをアンダーバーに置き換えて入力してください
#     例: flat chest -> flat_chest
#   ハイフンを含む単語が補完出来ない時はNotepad++の [設定] -> [環境設定] -> [区切り記号] -> [単語の一部と見なす文字を追加する] にハイフンを追加してください
#
# 注意点
#   スクリプトを実行中にもう一度スクリプトを実行すると、スクリプトが終了します
#   挙動がおかしい時は [プラグイン] -> [Python Script] -> [Show Console] の出力を確認してください
#     AutoComplete ENABLED for file: ... が表示されていない場合は有効化されていません

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
#   ESCAPE_CHAR: エスケープする特殊文字等
#   TEXT_SEPARATER: タグの末尾に付ける区切り文字
#   TRIM_SEPARATER_SPACE: タグと区切り文字の間にあるスペースを削除する
# //  VALID_SYMBOLS: 英数時以外の有効な記号(一部の文字 , ' 等は使用出来ません)
#   OPT_WORD_IN: タグ検索時の設定
#     - True: 部分一致(例: behindと入力した時にfrom_behindが候補に出る)
#     - False: 前方一致(例: behindと入力した時にfrom_behindは出ない)

TARGET_FILENAME = '.txt'
TAG_FILENAME = 'danbooru.csv'
NUM_SHOW = 2
MAX_SHOW_WORDS = 7
REPLACE_UB_TO_SPACE = True
ESCAPE_CHAR = '()'
TEXT_SEPARATER = ', '
TRIM_SEPARATER_SPACE = True
# // VALID_SYMBOLS = r'_-=+?!@.:)(><^\|/"' 
OPT_WORD_IN = True


class TagAutoComplete(object):
    _instance = None

    # ----------------------------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TagAutoComplete, cls).__new__(cls)
        return cls._instance

    # ----------------------------------------------------------------------------------------
    def __init__(self, csvfile):
        if not hasattr(self, 'initialized'):
            self.current_word = ""
            self.tags = self.read_tags_from_file(csvfile) # CSVファイルからタグを読み込み
            if len(self.tags):
                # BUFFERACTIVATED イベントが発生するたびに on_buffer_activated を呼び出すよう登録
                notepad.callback(self.on_buffer_activated, [NOTIFICATION.BUFFERACTIVATED])
                # スクリプト実行時に、現在開いているファイルに対して一度チェックを実行
                self.on_buffer_activated(None)
                console.write("tagAutoComplete has been activated.\n")

    # ----------------------------------------------------------------------------------------
    def destroy_instance(cls):
        if cls._instance:
            # 登録してあるコールバックを解除する
            notepad.clearCallbacks([NOTIFICATION.BUFFERACTIVATED])
            editor.clearCallbacks([SCINTILLANOTIFICATION.CHARADDED, SCINTILLANOTIFICATION.AUTOCSELECTION])

            console.write("tagAutoComplete has been deactivated.\n")
            cls._instance = None
        return cls._instance

    # ----------------------------------------------------------------------------------------
    def read_tags_from_file(self, filepath):
        """
        CSVファイルを読み込み、各行の最初の列から値を取得してリストを返す
        """

        tags = []
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    # 行が空でなく、かつ最初の列に値がある場合のみ処理
                    if row and row[0].strip():
                        tags.append(row[0].strip().decode('utf-8')) # UTF-8にデコードしてPythonのユニコード文字列として扱う

            console.write("Successfully loaded {} tags from {}\n".format(len(tags), os.path.basename(filepath)))

        except IOError:
            # ファイルが存在しない場合は、コンソールにメッセージを表示するだけ
            console.write("Info: {} not found. Skipping.\n".format(os.path.basename(filepath)))
            console.write("タグ補完に使用するファイルが無い\n")
            tags = []
        except Exception as e:
            # その他のエラーが発生した場合
            console.write("Error reading {}: {}\n".format(os.path.basename(filepath), e))
            console.write("タグ補完に使用するファイルが読み込めなかった\n")
            tags = []

        return tags

    # ----------------------------------------------------------------------------------------
    def get_current_word(self):
        """
        現在の単語(記号等も含めた有効なワード)を取得する
        # //  有効な文字[a-z][A-Z][0-9]とVALID_SYMBOLS
        """
        current_pos = editor.getCurrentPos()
        current_word = editor.getWord(current_pos, True)
        self.current_word = current_word # 項目選択後の処理の為にcurrent_wordをインスタンス変数にセットする(部分一致に対応するため)

        # -------------------
        # TODO
        # -------------------
        #
        # VALID_SYMBOLSの有効化
        # ()や{}等の処理をもうちょっとどうにかする
        # タグの強度(:1.1 みたいなの)を付けられるようにしたい



        return current_word


    # ----------------------------------------------------------------------------------------
    def on_char_added(self, args):
        """
        文字入力時の補完処理
        """
    
        current_word = self.get_current_word()
        if len(current_word) < NUM_SHOW:
            return

        suggestions = []
        for word in self.tags:
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
            current_sep = editor.autoCGetSeparator() # 現在のセパレーターの設定を取得する
            editor.autoCSetSeparator(44) # リストのセパレーターを','(Ascii:44)に変更する
            editor.autoCShow(0, ",".join(suggestions)) # 部分一致に対応するため入力済みの文字数を0にしている
            editor.autoCSetSeparator(current_sep) # セパレーターを元の設定に戻す


    # ----------------------------------------------------------------------------------------
    def on_buffer_activated(self, args):
        """
        ファイル（バッファ）が切り替わった時の処理
        """

        # バッファが切り替わった時は(二重に登録されてしまう事を防ぐため)一旦コールバックを解除する
        editor.clearCallbacks([SCINTILLANOTIFICATION.CHARADDED, SCINTILLANOTIFICATION.AUTOCSELECTION])

        # 特定のファイル名、または特定の拡張子のみで機能を有効化する
        current_filename = notepad.getCurrentFilename()
        if current_filename.endswith(TARGET_FILENAME):
            # 対象ファイルなら、コールバックを登録
            editor.callback(self.on_char_added, [SCINTILLANOTIFICATION.CHARADDED])
            editor.callback(self.on_autocompletion_selected, [SCINTILLANOTIFICATION.AUTOCSELECTION])
            console.write("AutoComplete ENABLED for file: {}\n".format(current_filename))


    # ----------------------------------------------------------------------------------------
    def process_string(self, s):
        """
        文字列を加工する
        """

        # アンダーバーをスペースに置換
        if REPLACE_UB_TO_SPACE:
            s = s.replace('_',' ')

        # 指定した文字をエスケープする
        for c in ESCAPE_CHAR:
            s = s.replace(c, '\\' + c)

        return s


    # ----------------------------------------------------------------------------------------
    def on_autocompletion_selected(self, args):
        """
        オートコンプリート項目選択後の加工処理
        """

        selected_text = args['text']
        max_len = editor.getLength()
        current_pos = editor.getCurrentPos()
        replace_start_pos = current_pos - len(self.current_word) - len(selected_text) # テキスト置換の開始位置(入力済み文字数 + メニューから選択した文字数 だけ戻る)
        replace_end_pos = current_pos

        output_text = self.process_string(selected_text) # 文字列を加工する

        # TRIM_SEPARATER_SPACEがTrueの時にタグと区切り文字の間の空白を削除する
        if TRIM_SEPARATER_SPACE is True:
            i = 0
            while current_pos + i < max_len:
                if editor.getTextRange(current_pos + i, current_pos + i + 1) != ' ':
                    replace_end_pos += i
                    break
                i += 1

        # 区切り文字が既に存在しているか確認する(既に区切り文字が存在する場合は新たに区切り文字を付与しない)
        if replace_end_pos + len(TEXT_SEPARATER) <= max_len:
            if editor.getTextRange(replace_end_pos, replace_end_pos + len(TEXT_SEPARATER)) != TEXT_SEPARATER:
                output_text = output_text + TEXT_SEPARATER
        else:
            output_text = output_text + TEXT_SEPARATER # ファイル末尾の時

        # 選択された元のテキストを、加工後のテキストで置き換える
        editor.setTargetRange(replace_start_pos, replace_end_pos)
        editor.replaceTarget(output_text)

        # カーソル位置を計算して移動
        editor.gotoPos(replace_start_pos + len(output_text))


# ----------------------------------------------------------------------------------------
# ディレクトリから指定したファイルの一覧を読み込む
# def get_filelist_from_dir(dir):
#    return








# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

    GLOBAL_TAC_INSTANCE = 'TAG_AUTO_COMPLETE_INSTANCE'

    if GLOBAL_TAC_INSTANCE in globals() and globals()[GLOBAL_TAC_INSTANCE]:
        # スクリプトが既に実行されている場合は終了する
        _tag_aut_comp = globals()[GLOBAL_TAC_INSTANCE]
        globals()[GLOBAL_TAC_INSTANCE] = _tag_aut_comp.destroy_instance()
    else:
        script_dir = os.path.dirname(__file__.decode('utf-8')) # パスが非ASCII文字を含む場合に備える
        csvfilepath = os.path.join(script_dir, TAG_FILENAME)
        globals()[GLOBAL_TAC_INSTANCE] = TagAutoComplete(csvfilepath)

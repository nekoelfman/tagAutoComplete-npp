# -*- coding: utf-8 -*-
# Notepad++ Python Script for tag auto-completion.

import os
import csv
from Npp import editor, notepad, console, SCINTILLANOTIFICATION, NOTIFICATION

# ----------------------------------------------------------------------------------------
#
# *** 利用前の設定 ***
#   - / や - 等の文字はNotepad++の標準の設定では単語の一部として認識されません
#   - 補完にそれらの文字を使用する場合は、Notepad++の [設定]->[環境設定]->[区切り記号]->[単語の一部と見なす文字を追加する] に文字を追加してください
#   - ワイルドカード補完機能を使用する場合は / の登録が必須です
#   - Notepad++全体に影響する設定ですので、他の機能に影響する可能性があります
#
# 説明
#   A1111やComfyUIでおなじみのTag Auto CompleteのNotepad++での実装を目指しています
#   ComfyUIのLoadTextノード等と合わせてご利用ください
#   Python Script plugin for Notepad++[https://github.com/bruderstein/PythonScript]を利用します
#     - Notepad++の [プラグイン]->[プラグイン管理] から PythonScript プラグインをインストールしてください
#     - PythonScriptのバージョン2.1で動作を確認しています
#   スクリプトと同じフォルダにあるファイルからタグ一覧を取得します
#     - CSVファイルの各行の一列目の値をタグとして扱います
#     - CSVファイルの一行目にヘッダー行がある場合は削除してください
#   スペースを含むタグを補完する時はスペースをアンダーバーに置き換えて入力してください
#     例: flat chest -> flat_chest
#   スクリプトを実行中にもう一度スクリプトを実行すると、スクリプトが終了します
#   挙動がおかしい時はNotepad++の [プラグイン]->[Python Script]->[Show Console] でコンソールの出力を確認してください
#     AutoComplete ENABLED for file: ... が表示されていない場合は有効化されていません
#
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
#   TEXT_SEPARATER: タグの末尾に付ける区切り文字(不要な場合は空にする)
#   TRIM_SEPARATER_SPACE: タグと区切り文字の間にあるスペースを削除する
#   OPT_WORD_IN: タグ検索時の設定
#     - True: 部分一致(例: behindと入力した時にfrom_behindが候補に出る)
#     - False: 前方一致(例: behindと入力した時にfrom_behindは出ない)
#   WILDCARD_DIR: ワイルドカードファイルが保存されているディレクトリ(空にするとワイルドカード入力の補完を無効化します)
#     - ワイルドカードファイルはテキスト形式(拡張子:txt)のみ対応しています
#   WILDCARD_ADD_SEPARATER: ワイルドカード補完時に末尾に区切り文字を付ける
#   LORA_DIR: Loraファイルが保存されているディレクトリ(空にするとLora入力の補完を無効化します)
#     - Loraファイルは(拡張子:safetensors)のみ対応しています
#   LORA_DEF_STRENGTH: Lora補完で使用するデフォルトのLoraの強度
#   LORA_ADD_SEPARATER: Lora補完時に末尾に区切り文字を付ける

TARGET_FILENAME = '.txt'
TAG_FILENAME = 'danbooru.csv'
NUM_SHOW = 2
MAX_SHOW_WORDS = 7
REPLACE_UB_TO_SPACE = True
ESCAPE_CHAR = '()'
TEXT_SEPARATER = ', '
TRIM_SEPARATER_SPACE = True
OPT_WORD_IN = True
WILDCARD_DIR = r'C:\my\wildcard'
WILDCARD_ADD_SEPARATER = True
LORA_DIR = r'C:\my\loras'
LORA_DEF_STRENGTH = '1'
LORA_ADD_SEPARATER = False


class TagManager(object):
    """
    タグファイル関連の操作を行なうクラス
    """

    # ----------------------------------------------------------------------------------------
    def __init__(self):
        self.tags = []

    # ----------------------------------------------------------------------------------------
    def load_tagfile(self, filepath):
        """
        タグファイルを読み込む
        filepath: タグファイルのパス
        """
        self.tags = []
        try:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():  # 行が空でなく、かつ最初の列に値がある場合のみ処理
                        self.tags.append(row[0].strip().decode('utf-8'))  # UTF-8にデコードしてPythonのユニコード文字列として扱う
            return True

        except IOError:
            # ファイルが存在しない場合は、コンソールにメッセージを表示するだけ
            console.write("Info: {} not found. Skipping.\n".format(os.path.basename(filepath)))
        except Exception as e:
            # その他のエラーが発生した場合
            console.write("Error reading {}: {}\n".format(os.path.basename(filepath), e))
        return False

    # ----------------------------------------------------------------------------------------
    def tag_suggest(self, s, max_num, word_in):
        """
        タグの補完候補一覧を返す
        s: 補完候補の取得に使用する文字列
        max_num: 取得するデータの最大個数
        word_in: Trueで部分一致、Falseで前方一致
        """

        suggestions = []
        ss = s.decode('utf-8').lower()
        for word in self.tags:
            if len(suggestions) >= max_num:
                break

            if OPT_WORD_IN: # 部分一致
                if ss in word.lower():
                    suggestions.append(word)
            else: # 前方一致
                if word.lower().startswith(ss):
                    suggestions.append(word)

        return suggestions

    def get_tag_num(self):
        """
        タグの個数を返す
        """
        return len(self.tags)


class WildcardManager(object):
    """
    Wildcard関連の操作を行なうクラス
    """

    # ----------------------------------------------------------------------------------------
    def __init__(self):
        self.dir_list = []
        self.txt_list = []  # *.txt (not support yaml)
        self.suggest_list = []

    # ----------------------------------------------------------------------------------------
    def load_wildcards(self, d):
        """
        wildcardファイル、ディレクトリの一覧を取得
        d: wildcardディレクトリのパス
        """
        if not os.path.exists(d):
            return False
        self.dir_list = []
        self.txt_list = []
        self.suggest_list = []

        # ディレクトリとファイルのリストを取得する
        d_len = len(d) if d.endswith('\\') else len(d) + 1
        for dirpath, dirname, files in os.walk(d):
            self.dir_list.append(dirpath[d_len:].replace('\\','/'))  # ディレクトリパスを整形してリストに追加
            for file in files:
                if file.endswith('.txt'):
                    s = os.path.join(dirpath,file)
                    self.txt_list.append(s[d_len:].replace('\\','/').replace('.txt',''))  # ファイルパスを整形してリストに追加
        self.suggest_list = sorted(list(filter(None, self.dir_list + self.txt_list)))

        return True

    # ----------------------------------------------------------------------------------------
    def wildcard_suggest(self, s, max_num, word_in):
        """
        wildcardの補完候補一覧を返す
        s: 補完候補の取得に使用する文字列
        max_num: 取得するデータの最大個数
        word_in: Trueで部分一致、Falseで前方一致
        """
        suggestions = []
        ss = s[2:].decode('utf-8').lower()  # 検索文字列の整形(先頭の__を削る、小文字化)
        for word in self.suggest_list:
            if len(suggestions) >= max_num:
                break

            if word_in:
                if ss in word.lower():
                    suggestions.append(word)  # 部分一致した候補をリストに追加
            else:
                if word.lower().startswith(ss):
                    suggestions.append(word)  # 前方一致した候補をリストに追加

        return suggestions

    # ----------------------------------------------------------------------------------------
    def item_is_dir(self, s):
        """
        候補がディレクトリかファイルかを判別する
        s: 調査する候補
        """
        return s in self.dir_list

    # ----------------------------------------------------------------------------------------
    def get_wildcard_num(self):
        """
        ワイルドカードの個数(ディレクトリとファイルの数)を返す
        """
        return len(self.suggest_list)


class LoraManager(object):
    """
    Lora関連の操作を行なうクラス
    """

    # ----------------------------------------------------------------------------------------
    def __init__(self):
        self.lorafile_list = []  # *.safetensors or *.pt
        self.suggest_list = []

    # ----------------------------------------------------------------------------------------
    def load_loras(self, d):
        """
        Loraファイル、ディレクトリの一覧を取得
        d: Loraディレクトリのパス
        """
        if not os.path.exists(d):
            return False
        self.lorafile_list = []
        self.suggest_list = []

        # ディレクトリとファイルのリストを取得する
        d_len = len(d) if d.endswith('\\') else len(d) + 1
        for dirpath, dirname, files in os.walk(d):
            for file in files:
                if file.endswith('.safetensors'):
                    s = os.path.join(dirpath,file)
                    self.lorafile_list.append(s[d_len:].replace('\\','/').replace('.safetensors',''))  # ファイルパスを整形してリストに追加
        self.suggest_list = sorted(list(filter(None, self.lorafile_list)))

        return True

    # ----------------------------------------------------------------------------------------
    def lora_suggest(self, s, max_num, word_in):
        """
        wildcardの補完候補一覧を返す
        s: 補完候補の取得に使用する文字列
        max_num: 取得するデータの最大個数
        word_in: Trueで部分一致、Falseで前方一致
        """
        suggestions = []
        ss = s[4:].decode('utf-8').lower()  # 検索文字列の整形(先頭の____を削る、小文字化)
        for word in self.suggest_list:
            if len(suggestions) >= max_num:
                break

            if word_in:
                if ss in word.lower():
                    suggestions.append(word)  # 部分一致した候補をリストに追加
            else:
                if word.lower().startswith(ss):
                    suggestions.append(word)  # 前方一致した候補をリストに追加

        return suggestions

    # ----------------------------------------------------------------------------------------
    def get_loras_num(self):
        """
        Loraファイルの個数を返す
        """
        return len(self.suggest_list)



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

            self.wcm = WildcardManager()
            if WILDCARD_DIR:
                if self.wcm.load_wildcards(WILDCARD_DIR):  # Wildcard一覧を指定したディレクトリから取得する
                    console.write("Successfully loaded {} wildcards(dirs and files) from {}\n".format(self.wcm.get_wildcard_num(), WILDCARD_DIR))

            self.lom = LoraManager()
            if LORA_DIR:
                if self.lom.load_loras(LORA_DIR):  # Lora一覧を指定したディレクトリから取得する
                    console.write("Successfully loaded {} Loras from {}\n".format(self.lom.get_loras_num(), LORA_DIR))

            self.tm = TagManager()
            if self.tm.load_tagfile(csvfile):
                console.write("Successfully loaded {} tags from {}\n".format(self.tm.get_tag_num(), os.path.basename(csvfile)))
                console.write("tagAutoComplete has been activated.\n")
                # BUFFERACTIVATED イベントが発生するたびに on_buffer_activated を呼び出すよう登録
                notepad.callback(self.on_buffer_activated, [NOTIFICATION.BUFFERACTIVATED])
                self.on_buffer_activated(None)  # スクリプト起動時に現在開いているファイルに対してon_buffer_activatedを実行

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
    def on_char_added(self, args):
        """
        文字入力時の補完処理
        """
        self.current_word = editor.getWord(editor.getCurrentPos(), True)  # 現在の単語(Notepad++が単語として認識する文字列)を取得する
        if len(self.current_word) < NUM_SHOW:
            return  # 最低入力文字数に達してない

        if self.current_word.startswith('____') and LORA_DIR:  # Lora補完
            suggestions = self.lom.lora_suggest(self.current_word, MAX_SHOW_WORDS, OPT_WORD_IN)
        elif self.current_word.startswith('__') and WILDCARD_DIR:  # ワイルドカード補完
            suggestions = self.wcm.wildcard_suggest(self.current_word, MAX_SHOW_WORDS, OPT_WORD_IN)
        else:  # タグ補完
            suggestions = self.tm.tag_suggest(self.current_word, MAX_SHOW_WORDS, OPT_WORD_IN)

        # 候補が存在する時にメニューを表示
        if suggestions:
            current_sep = editor.autoCGetSeparator() # Notepad++のセパレーター設定を取得する
            editor.autoCSetSeparator(44) # セパレーター設定を','(Ascii:44)に変更する
            editor.autoCShow(0, ",".join(suggestions)) # 部分一致に対応するため入力済みの文字数を0にしている
            editor.autoCSetSeparator(current_sep) # セパレーター設定を元に戻す

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
        s: オートコンプリートで選択された候補の文字列
        """
        if self.current_word.startswith('____') and LORA_DIR:  # Loraの加工処理
            sep_pos = s.rfind('/')
            if not sep_pos == -1:
                s = s[sep_pos+1:]  # ファイル名だけを取得する
            s = '<lora:' + s + ':' + LORA_DEF_STRENGTH + '>'
        elif self.current_word.startswith('__') and WILDCARD_DIR:  # ワイルドカードの加工処理
            if self.wcm.item_is_dir(s):
                s = s + '/*'  # 候補がディレクトリの場合は末尾に /* を付ける
            s = '__' + s + '__'
        else:
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

        # 区切り文字の追加処理
        add_sep = True
        if replace_end_pos + len(TEXT_SEPARATER) <= max_len:  # ファイルの末尾ではない時
            if editor.getTextRange(replace_end_pos, replace_end_pos + len(TEXT_SEPARATER)) == TEXT_SEPARATER:  # すでに区切り文字が存在する
                add_sep = False
        if self.current_word.startswith('____') and LORA_DIR:
            add_sep = LORA_ADD_SEPARATER
        elif self.current_word.startswith('__') and WILDCARD_DIR:
            add_sep = WILDCARD_ADD_SEPARATER
        if add_sep:
            output_text += TEXT_SEPARATER  # 区切り文字を追加

        # 選択された元のテキストを、加工後のテキストで置き換える
        editor.setTargetRange(replace_start_pos, replace_end_pos)
        editor.replaceTarget(output_text)

        # カーソル位置を計算して移動
        editor.gotoPos(replace_start_pos + len(output_text))



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

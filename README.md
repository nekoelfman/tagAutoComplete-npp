# tag-autocomplete-npp
Tag Auto Completion for Notepad++ Python Script.

![](screenshot_01.png)

tag-autocomplete-npp はNotepad++上に入力補完機能(いわゆるTag Autocomplete)を実装するスクリプトです。

## 導入方法
- Notepad++用のプラグイン [Python Script](https://github.com/bruderstein/PythonScript) を利用します。事前にNotepad++に導入してください。
- tagAutoComplete.py を PythonScript の User Scripts フォルダに入れてください。
  - Notepad++の設定を変えていなければ %APPDATA%\Notepad++\plugins\config\PythonScript\scripts
- タグ情報の入ったCSVファイルを同じフォルダに置いてください。
  - CSVファイルの各行の一番左側の値をタグとして扱います(二番目以降の値は利用しません)。
  - CSVファイルの一行目にヘッダー行がある場合は削除してください。
  - 上の方にあるデータから優先的に表示します。
  - __付属のdanbooru.csvはサンプルです。適当なデータをご用意ください。__
- Notepad++のメニューから 「プラグイン」->「Python Script」->「Scripts」->「tagAutoComplete」で実行
  - 対象のファイルを開いた時に自動で有効化されます。
- デフォルト設定
  - ファイル名の末尾が '.txt' になっているファイルで入力補完を有効化
  - 同じフォルダにある 'danbooru.csv' からタグ一覧を読み込む
  - 2文字目から補完メニューを表示する
  - メニューに表示する候補数:7
  - アンダーバーを半角スペースに置き換え
  - 前方一致で検索

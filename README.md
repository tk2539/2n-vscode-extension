# 2n Script VSCode Extension

`2n Script` は独自構文で設計された軽量スクリプト言語です。  
この拡張機能を導入することで、`.2n` ファイルを VSCode から直接実行することができます。

---

## 特徴

- `.2n` 拡張子を自動認識
- キーワードハイライト付き
- 上部に実行ボタンを表示
- ターミナルで `main.py` を通してスクリプト実行
- 構文エラーが出た場合もターミナルに表示

---

## 使用方法

1. この拡張機能を VSCode にインストール（VSIX）
2. `.2n` ファイルを作成・開く
3. 上部の `Run 2n Script` ボタンをクリック！

---

## サンプル（おみくじ）

```2n
input x = 1
for 100
{
  addlist list.all = x
  input x = (x + 1)
}

function roll
{
  input result = random[list.all]
  if ?(result <= 25)
  {
    print "大吉"
  }
  else if ?(result <= 64)
  {
    print "吉"
  }
  else
  {
    print "凶"
  }
}

for 10
{
  action roll()
}
```

---

## 実行画面

下図は、実際に `.2n` ファイルを VSCode 上で実行した出力結果です。

![実行画面](https://raw.githubusercontent.com/tk2539/2n-vscode-extension/main/images/omikuji-test.png)

---

## 拡張機能のインストール方法

1. `vsce` でパッケージ化された `.vsix` を入手
2. 以下のコマンドでインストール：

```bash
code --install-extension 2n-script-runner-0.1.0.vsix
```

または、VSCodeの拡張機能メニューから「VSIXからインストール」を選んでください。

---

## ファイル構成（例）

```
2n-vscode-extension/
├── main.py                  ← スクリプト処理エンジン
├── README.md
├── package.json
├── src/
├── out/
└── syntaxes/
```

---

## 開発者向け：ビルド方法

```bash
npm install
npx esbuild src/extension.ts --bundle --outfile=out/extension.js --platform=node --external:vscode
```

---

## ライセンスと作者

本拡張機能および 2n Script は個人プロジェクト「2n Project」として開発されました。  
ぜひ教育・ツール・創作など幅広くご活用ください！


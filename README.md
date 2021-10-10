# AWS-StepFunctions_MultipleResourcesStart-StopControl

## 概要

- EC2とRDS(Aurora)を、グループ単位かつ指定した順番に起動/停止する仕組みを AWS Step FunctionsとLambda(Python 3.9)で作りました。
- 作成した StepFunctions ステートマシン の詳細を説明します。
- 以下のように複数のEC2,RDS(Aurora)がある場合に、タグを使いをグループ化と起動順序を設定します。
- タグに必要な情報を設定し、起動したいグループと命令(起動命令 or 停止命令)を指定すると、順番に従いリソースを起動or 停止します。
- 詳細はQiitaをみてください
    - https://qiita.com/suo-takefumi/items/6c58f2cc071a9d7da83a
# 実行例

StepFunctions実行時の `実行入力` は ↓ です。

```json
{
  "EXEC": "stop",
  "DATE": "2021-10-09T21:40:00+09:00",
  "GroupTag": "Group",
  "GroupValue": "test2",
  "BootOrderTag": "BootOrder"
}
```

`実行入力` の各要素の意味

|要素|説明|
|---|---|
|EXEC|実行命令 `start` or `stop`|
|DATE|実行日時 `YYYY-MM-DDThh:mm:ss+09:00`<BR />例 `2021-10-09T21:40:00+09:00`<BR />`now` ←即時実行の場合 |
|GroupTag|グループ分けのタグ|
|GroupValue|グループ名|
|BootOrderTag|起動順番のタグ|

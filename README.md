# AWS-StepFunctions_MultipleResourcesStart-StopControl

- EC2とRDS(Aurora)を、グループ単位かつ指定した順番に起動/停止する仕組みを AWS Step FunctionsとLambda(Python 3.9)で作りました。
- 作成した StepFunctions ステートマシン の詳細を説明します。
- 以下のように複数のEC2,RDS(Aurora)がある場合に、タグを使いをグループ化と起動順序を設定します。
- タグに必要な情報を設定し、起動したいグループと命令(起動命令 or 停止命令)を指定すると、順番に従いリソースを起動or 停止します。


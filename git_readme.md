# Git 代码管理流程记录

本文档记录了将 `开关柜局放软件_v2` 项目初始化为 Git 仓库并推送到远程 GitHub 仓库的操作步骤。

## 步骤

1.  **进入项目目录**:
    首先，使用命令行工具 (如 CMD, PowerShell, Git Bash) 进入项目所在的文件夹。
    ```bash
    cd e:\trae_test\开关柜局放软件_v2
    ```

2.  **初始化 Git 仓库**:
    在项目根目录下执行 `git init` 命令，初始化本地 Git 仓库。这会创建一个 `.git` 隐藏文件夹。
    ```bash
    git init
    ```

3.  **添加文件到暂存区**:
    使用 `git add .` 命令将当前目录下所有文件添加到 Git 的暂存区。
    ```bash
    git add .
    ```

4.  **提交更改到本地仓库**:
    使用 `git commit` 命令将暂存区的文件提交到本地仓库，并附带一条提交信息（`-m` 参数）。
    ```bash
    git commit -m "Initial commit"
    ```

5.  **关联远程仓库**:
    将本地仓库与远程 GitHub 仓库关联起来。使用 `git remote add` 命令，`origin` 是远程仓库的默认别名，后面跟上远程仓库的 URL。
    ```bash
    git remote add origin https://github.com/yangyuqing15715165798/trae_tev_aa_uhf_v1
    ```

6.  **检查本地分支名称**:
    在推送前，确认当前本地分支的名称。默认通常是 `master` 或 `main`。
    ```bash
    git branch
    ```
    (输出结果中带 `*` 号的就是当前分支，例如 `* master`)

7.  **推送到远程仓库**:
    使用 `git push` 命令将本地分支的提交推送到远程仓库 `origin`。`-u` 参数会建立本地分支与远程分支的跟踪关系，方便以后直接使用 `git push`。根据步骤 6 确认的分支名称（假设是 `master`）进行推送。
    ```bash
    git push -u origin master
    ```
    *如果你的分支名称是 `main`，则使用 `git push -u origin main`*

完成以上步骤后，项目的代码就已经成功上传并托管在 GitHub 远程仓库中了。

**原因:**
这个错误表示你的远程仓库（例如 GitHub 上的仓库）包含了你本地仓库当前没有的提交或更改。这通常发生在其他人向远程仓库推送了更新，或者你直接在远程仓库（如 GitHub 网站）上做了修改（比如编辑 README）。Git 为了防止你的本地提交覆盖掉远程的新内容，拒绝了直接推送。

**解决方法:**
你需要先将远程仓库的最新更改拉取到本地，与你的本地更改合并后，再进行推送。

1.  **拉取并合并远程更改**:
    执行 `git pull` 命令，将远程 `origin` 仓库的 `master` (或 `main`) 分支的最新内容拉取下来并尝试与本地分支合并。
    ```bash
    git pull origin master
    ```
    *如果你的分支是 `main`，则使用 `git pull origin main`*
    *   **注意**: 如果本地和远程都修改了同一个文件的相同部分，可能会发生**合并冲突 (merge conflict)**。你需要根据 Git 的提示手动解决这些冲突，然后再次执行 `git add .` 和 `git commit` 来完成合并。

2.  **再次推送**:
    成功拉取并合并（解决冲突后）之后，你的本地仓库就既包含了远程的更新，也包含了你自己的提交。现在可以再次尝试推送：
    ```bash
    git push origin master
    ```
    *如果你的分支是 `main`，则使用 `git push origin main`*
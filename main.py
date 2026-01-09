# -*- encoding:utf-8 -*-
# auth:tomato
import json, os, subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QPushButton, QFormLayout,
    QCheckBox, QComboBox, QMessageBox, QLabel
)
from PySide6.QtGui import QIcon

CONFIG_FILE = "config.json"

def run_tool(tool):
    env = os.environ.copy()
    if "env" in tool:
        for k, v in tool["env"].items():
            env[k] = v.replace("$PATH", env.get("PATH", ""))

    if not tool.get("open_cmd", True):
        # 不在 CMD 中运行，直接执行命令
        subprocess.Popen(
            tool["cmd"], cwd=tool["workdir"], shell=True, env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # 在 CMD 中运行
        cmdline = tool.get("cmd", "").strip()
        if not cmdline:
            subprocess.Popen("start cmd", cwd=tool["workdir"], shell=True)
        else:
            mode = tool.get("run_in_cmd", "exec")
            if mode == "echo":
                subprocess.Popen(f'start cmd /k "echo {cmdline}"', cwd=tool["workdir"], shell=True)
            else:
                subprocess.Popen(f'start cmd /k "echo {cmdline} & echo. & {cmdline}"', cwd=tool["workdir"], shell=True)

class Toolbox(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工具箱")
        self.resize(1500, 800)

        main_layout = QHBoxLayout(self)

        # 左边：分类树
        left_layout = QVBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索工具...")
        left_layout.addWidget(self.search)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        left_layout.addWidget(self.tree)

        # 右边：工具详情编辑区
        right_layout = QVBoxLayout()
        self.detail_label = QLabel("<b>工具详情</b>")
        right_layout.addWidget(self.detail_label)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.cat_edit = QLineEdit()
        self.cmd_edit = QLineEdit()
        self.dir_edit = QLineEdit()
        self.run_in_cmd_check = QCheckBox("不在 CMD 中运行")
        self.run_mode_combo = QComboBox()
        self.run_mode_combo.addItems(["exec", "echo"])

        form.addRow("名称*:", self.name_edit)
        form.addRow("类别:", self.cat_edit)
        form.addRow("命令:", self.cmd_edit)
        form.addRow("目录*:", self.dir_edit)
        form.addRow(self.run_in_cmd_check)
        form.addRow("Run Mode:", self.run_mode_combo)
        right_layout.addLayout(form)

        self.save_btn = QPushButton("保存修改")
        self.new_btn = QPushButton("新增工具")
        self.del_btn = QPushButton("删除工具")
        right_layout.addWidget(self.save_btn)
        right_layout.addWidget(self.new_btn)
        right_layout.addWidget(self.del_btn)
        right_layout.addStretch()

        # 主布局拼接
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(left_widget, 3)
        main_layout.addWidget(right_widget, 4)

        # 加载配置
        self.load_config()

        # 信号槽
        self.search.textChanged.connect(self.refresh_list)
        self.tree.itemDoubleClicked.connect(self.launch)
        self.tree.itemClicked.connect(self.show_tool_detail)
        self.save_btn.clicked.connect(self.save_tool)
        self.new_btn.clicked.connect(self.new_tool)
        self.del_btn.clicked.connect(self.delete_tool)
        self.run_in_cmd_check.stateChanged.connect(self.update_run_mode_state)

        self.current_tool = None

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.tools = json.load(f)
        else:
            self.tools = []
        self.refresh_list()

    def refresh_list(self):
        keyword = self.search.text().lower()
        self.tree.clear()
        categories = {}
        for tool in self.tools:
            if keyword not in tool["name"].lower():
                continue
            cat_name = tool.get("category", "未分类")
            if cat_name not in categories:
                cat_item = QTreeWidgetItem([cat_name])
                self.tree.addTopLevelItem(cat_item)
                categories[cat_name] = cat_item

            item = QTreeWidgetItem([tool["name"]])
            item.setIcon(0, QIcon(tool.get("icon", "")))
            item.setData(0, 1000, tool)
            categories[cat_name].addChild(item)

        self.tree.expandAll()

    def launch(self, item, column):
        tool = item.data(0, 1000)
        if tool:
            run_tool(tool)

    def show_tool_detail(self, item, column):
        tool = item.data(0, 1000)
        if not tool:
            return

        # 保证 self.current_tool 指向原始对象
        for t in self.tools:
            if t["name"] == tool.get("name") and t.get("workdir") == tool.get("workdir"):
                self.current_tool = t
                break
        else:
            self.current_tool = tool

        self.name_edit.setText(self.current_tool.get("name", ""))
        self.cat_edit.setText(self.current_tool.get("category", "未分类"))
        self.cmd_edit.setText(self.current_tool.get("cmd", ""))
        self.dir_edit.setText(self.current_tool.get("workdir", ""))
        self.run_in_cmd_check.setChecked(not self.current_tool.get("not_in_cmd", False))
        self.run_mode_combo.setCurrentText(self.current_tool.get("run_in_cmd", "exec"))
        self.update_run_mode_state()

    def update_run_mode_state(self):
        if self.run_in_cmd_check.isChecked():
            self.run_mode_combo.setCurrentText("")
            self.run_mode_combo.setEnabled(False)
        else:
            self.run_mode_combo.setEnabled(True)
            if not self.run_mode_combo.currentText():
                self.run_mode_combo.setCurrentText("exec")

    def save_tool(self):
        if not self.current_tool:
            QMessageBox.warning(self, "提示", "请先选择一个工具")
            return
        name = self.name_edit.text().strip()
        workdir = self.dir_edit.text().strip()
        if not name or not workdir:
            QMessageBox.warning(self, "提示", "名称和目录为必填项")
            return

        self.current_tool["name"] = name
        self.current_tool["category"] = self.cat_edit.text().strip() or "未分类"
        self.current_tool["cmd"] = self.cmd_edit.text().strip()
        self.current_tool["workdir"] = workdir
        self.current_tool["not_in_cmd"] = not self.run_in_cmd_check.isChecked()
        self.current_tool["open_cmd"] = not self.run_in_cmd_check.isChecked()
        self.current_tool["run_in_cmd"] = self.run_mode_combo.currentText() if not self.run_in_cmd_check.isChecked() else ""

        self.save_config()
        self.load_config()
        QMessageBox.information(self, "成功", "保存成功")

    def new_tool(self):
        new_tool = {
            "name": "",
            "icon": "cmd.png",
            "cmd": "",
            "workdir": "",
            "open_cmd": True,
            "not_in_cmd": False,
            "run_in_cmd": "exec",
            "category": ""
        }
        self.tools.append(new_tool)
        self.current_tool = new_tool
        self.show_tool_detail(QTreeWidgetItem([new_tool["name"]]), 0)
        self.name_edit.setFocus()
        self.refresh_list()

    def delete_tool(self):
        if not self.current_tool:
            QMessageBox.warning(self, "提示", "请先选择一个工具")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定删除工具 '{self.current_tool['name']}' ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tools.remove(self.current_tool)
            self.current_tool = None
            self.clear_detail()
            self.save_config()
            self.refresh_list()

    def clear_detail(self):
        self.name_edit.clear()
        self.cat_edit.clear()
        self.cmd_edit.clear()
        self.dir_edit.clear()
        self.run_in_cmd_check.setChecked(False)
        self.update_run_mode_state()

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tools, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    app = QApplication([])
    win = Toolbox()
    win.show()
    app.exec()

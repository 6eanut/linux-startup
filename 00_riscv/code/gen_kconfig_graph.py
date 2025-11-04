import json
from pyvis.network import Network

# 文件路径
all_config_file = "all_config.txt"
config_tree_file = "configtree.json"

MAX_DEPTH = 20

# 读取文件
with open(all_config_file) as f:
    all_configs = [line.strip() for line in f if line.strip()]

with open(config_tree_file) as f:
    dep_tree = json.load(f)

# 初始化交互图
net = Network(height="850px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
net.toggle_physics(True)

visited = set()

def add_dependencies(cfg, depth=0):
    if depth > MAX_DEPTH or cfg in visited:
        return
    visited.add(cfg)

    color = "#ADD8E6" if cfg in all_configs else "#FFB6C1"
    net.add_node(cfg, label=cfg, color=color, title=f"{cfg}")

    for parent in dep_tree.get(cfg, []):
        parent_color = "#ADD8E6" if parent in all_configs else "#FFB6C1"
        net.add_node(parent, label=parent, color=parent_color, title=f"{parent}")
        net.add_edge(parent, cfg)
        add_dependencies(parent, depth + 1)

for cfg in all_configs:
    add_dependencies(cfg)

# 确保孤立节点也显示
for cfg in all_configs:
    if cfg not in dep_tree or not dep_tree[cfg]:
        net.add_node(cfg, label=cfg, color="#ADD8E6", title=f"{cfg}")

# 生成 HTML
output_file = "kconfig_dependency_graph.html"
net.write_html(output_file)

# ------------------------------
# 手动在 HTML 文件里注入点击高亮脚本
# ------------------------------
custom_js = """
<script type="text/javascript">
// 点击节点时高亮依赖链
network.on("click", function(params) {
    if (params.nodes.length > 0) {
        var clickedNode = params.nodes[0];
        var connectedEdges = network.getConnectedEdges(clickedNode);
        var connectedNodes = network.getConnectedNodes(clickedNode);
        // 重置所有节点颜色
        nodes.update(nodes.get().map(n => ({
            id: n.id,
            color: (n.color === '#ADD8E6' || n.color === '#FFB6C1') ? n.color : '#d3d3d3'
        })));
        // 高亮当前节点及依赖链
        nodes.update(connectedNodes.map(id => ({id: id, color: '#FFD700'})));
        nodes.update([{id: clickedNode, color: '#FFA500'}]);
    }
});
</script>
"""

# 将脚本插入到 HTML 文件末尾
with open(output_file, "r", encoding="utf-8") as f:
    html_content = f.read()

html_content = html_content.replace("</body>", custom_js + "\n</body>")

with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ 生成完毕：{output_file}")

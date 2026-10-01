# 留出执行记录

四个新原生窗口已取得，45.662秒，均正确UInt16/CRS/affine、无重采样，
ZIP CRC/来源SHA已保存，全部natural NoData0。方法、q、窗口和45项
配置不变；此数据获取本身不是方法结果。

获取前两次启动被clean/pushed guard拒绝，未创建source目录或读取
新像元。原因是Git push尚未完成就发起获取；保留两个guard日志。
GitHub通过原代理连接停顿，终止的只是本任务自己的Git进程，改用
**单命令**NO_PROXY访问GitHub，不改用户全局代理。确认push完成后，
唯一真实获取从49109985a22c4608fe8b5167245d20976d882a5b启动。

初实验freeze在5f7f3aa26609cc88ef7c5ab8234dcd1aecf58ad6保存，未编码。
实际编码前发现launch记录应只保存明确科学环境键，而不是整个父
process environment；修正该日志行为，旧freeze另存initial文件，
重新绑定并推送。未输出父环境、未改变科学参数、未运行再挑结果。
最终有效freeze由`heldout_experiment_preflight_20261001.json`给出。

-- 2025-08-26 20:00:00
-- 保留近5年数据
-- 清理策略：插入于 2020-01-01 00:00:00（数据库服务器的当地时区） 之前的记录
-- 手动查询需要清理的表的最大ID值
-- 注意：
-- 1. 有的表可能无法以日期字段进行查询，日期字段为空或人为修改过
-- 2. 可通过表的业务含义从其他业务表中通过关联查询到最大ID值

-- 仓库货物清单表 base_warehouse_and_tk
-- 查看表结构
desc base_warehouse_and_tk;

-- 查看表数据
select * from base_warehouse_and_tk limit 1;

-- 查询创建时间早于 2020-01-01 00:00:00 的记录中的最大ID值
select max(id) AS max_id from base_warehouse_and_tk where create_time < '2020-01-01 00:00:00';

-- 查询创建时间早于 2022-01-01 00:00:00 的记录中的最大ID值
select max(id) AS max_id from base_warehouse_and_tk where create_time < '2022-01-01 00:00:00';






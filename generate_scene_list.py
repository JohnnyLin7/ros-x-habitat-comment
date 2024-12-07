import os
import csv
import gzip
import json
from habitat.config.default import get_config

def generate_scene_csv(config_path, output_csv):
    # 加载配置文件
    config = get_config(config_path)
    
    # 读取数据集文件
    dataset_path = config.DATASET.DATA_PATH.format(split=config.DATASET.SPLIT)
    print(f"正在读取数据集: {dataset_path}")
    
    # 读取gzip压缩的json文件
    with gzip.open(dataset_path, 'rt') as f:
        dataset = json.load(f)
    
    # 统计场景信息
    all_scenes = set()
    for episode in dataset['episodes']:
        all_scenes.add(episode['scene_id'])
    print(f"数据集中总场景数: {len(all_scenes)}")
    print(f"数据集中总episode数: {len(dataset['episodes'])}")
    
    # 用字典记录每个场景的第一个episode
    scene_to_episode = {}
    for episode in dataset['episodes']:
        scene_id = episode['scene_id']
        if scene_id not in scene_to_episode:
            scene_to_episode[scene_id] = {
                'episode_id': str(episode['episode_id']),
                'scene_id': scene_id
            }
    
    # 将字典转换为列表
    csv_data = list(scene_to_episode.values())
    
    # 写入CSV文件
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['episode_id', 'scene_id'])
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"已生成CSV文件，包含 {len(csv_data)} 个场景")
    print("场景列表:")
    for scene in sorted(all_scenes):
        print(f"- {scene}")

if __name__ == "__main__":
    config_path = "/home/johnnylin/ros_x_habitat_ws/src/ros_x_habitat/configs/setting_2_configs/pointnav_rgbd-mp3d.yaml"
    output_csv = "/home/johnnylin/ros_x_habitat_ws/src/ros_x_habitat/val_episodes_list.csv"
    
    generate_scene_csv(config_path, output_csv)
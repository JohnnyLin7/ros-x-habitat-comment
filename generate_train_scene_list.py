import os
import csv
import gzip
import json
import glob
from habitat.config.default import get_config

def generate_scene_csv(config_path, output_csv):
    # 加载配置文件
    config = get_config(config_path)
    
    # 获取训练数据集的content目录路径
    dataset_base_path = config.DATASET.DATA_PATH.format(split=config.DATASET.SPLIT)
    content_dir = os.path.join(os.path.dirname(dataset_base_path), "content")
    print(f"正在读取content目录: {content_dir}")
    
    # 获取所有场景的json.gz文件
    scene_files = glob.glob(os.path.join(content_dir, "*.json.gz"))
    print(f"找到 {len(scene_files)} 个场景文件")
    
    # 用于存储所有场景的episode信息
    scene_to_episode = {}
    all_scenes = set()
    total_episodes = 0
    
    # 读取每个场景文件
    for scene_file in scene_files:
        scene_id = os.path.splitext(os.path.splitext(os.path.basename(scene_file))[0])[0]
        print(f"处理场景: {scene_id}")
        
        # 读取场景的json.gz文件
        with gzip.open(scene_file, 'rt') as f:
            scene_data = json.load(f)
            
        # 统计场景信息
        all_scenes.add(scene_id)
        total_episodes += len(scene_data['episodes'])
        
        # 遍历场景中的所有episodes,找到属于该场景的episode
        for episode in scene_data['episodes']:
            if episode['scene_id'].endswith(f"{scene_id}/{scene_id}.glb"):
                scene_to_episode[scene_id] = {
                    'episode_id': str(episode['episode_id']),
                    'scene_id': f"data/scene_datasets/mp3d/{scene_id}/{scene_id}.glb"
                }
                break
    
    # 将字典转换为列表
    csv_data = list(scene_to_episode.values())
    
    # 写入CSV文件
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['episode_id', 'scene_id'])
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"\n统计信息:")
    print(f"总场景数: {len(all_scenes)}")
    print(f"总episode数: {total_episodes}")
    print(f"已生成CSV文件，包含 {len(csv_data)} 个场景")
    print("\n场景列表:")
    for scene in sorted(all_scenes):
        print(f"- {scene}")

if __name__ == "__main__":
    config_path = "/home/johnnylin/ros_x_habitat_ws/src/ros_x_habitat/configs/pointnav_mp3d.yaml"
    output_csv = "/home/johnnylin/ros_x_habitat_ws/src/ros_x_habitat/episodes_list_train.csv"
    
    generate_scene_csv(config_path, output_csv)
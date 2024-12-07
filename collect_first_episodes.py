import json
import glob
import gzip
import os

def collect_first_episodes():
    # 定义路径
    content_dir = "/home/johnnylin/ros_x_habitat_ws/src/ros_x_habitat/data/datasets/pointnav/mp3d/v1/train/content"
    output_path = "/home/johnnylin/ros_x_habitat_ws/src/ros_x_habitat/data/datasets/pointnav/mp3d/v1/train/train.json.gz"
    
    # 检查目录是否存在
    if not os.path.exists(content_dir):
        print(f"错误：目录 {content_dir} 不存在")
        return
        
    # 获取所有.json.gz文件
    scene_files = glob.glob(os.path.join(content_dir, "*.json.gz"))
    
    # 检查是否找到文件
    if not scene_files:
        print(f"警告：在 {content_dir} 目录下没有找到.json.gz文件")
        return
        
    print(f"找到 {len(scene_files)} 个场景文件")
    
    # 存储所有第一个episode
    all_first_episodes = []
    
    # 读取每个文件
    for scene_file in scene_files:
        try:
            with gzip.open(scene_file, 'rt') as f:
                data = json.load(f)
                print(f"处理文件: {scene_file}")
                if 'episodes' in data:
                    # 检查第一个episode的结构
                    if data['episodes']:
                        first_episode = data['episodes'][0]
                        print(f"第一个episode的episode_id: {first_episode['episode_id']}")
                        print(f"episode_id的类型: {type(first_episode['episode_id'])}")
                        # 修改比较方式
                        if first_episode['episode_id'] == 0 or first_episode['episode_id'] == "0":
                            all_first_episodes.append(first_episode)
                            print(f"成功添加一个episode从文件: {scene_file}")
        except Exception as e:
            print(f"处理文件 {scene_file} 时出错: {str(e)}")
    
    print(f"总共收集到 {len(all_first_episodes)} 个episodes")
    
    # 创建新的数据结构
    output_data = {
        "episodes": all_first_episodes
    }
    
    # 保存为gzip压缩的JSON文件
    try:
        with gzip.open(output_path, 'wt') as f:
            json.dump(output_data, f)
        print(f"成功保存 {len(all_first_episodes)} 个episodes到 {output_path}")
    except Exception as e:
        print(f"保存文件时出错: {str(e)}")

if __name__ == "__main__":
    collect_first_episodes()
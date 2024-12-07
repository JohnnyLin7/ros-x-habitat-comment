import argparse
import os
from habitat.config.default import get_config
from src.evaluators.habitat_evaluator import HabitatEvaluator
from src.utils import utils_visualization, utils_files
from typing import Dict, List
import numpy as np
import signal
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)


def load_unique_scene_episodes(file_path: str, has_header: bool = False):
    """Load episode identifiers but only keep one episode per unique scene."""
    episode_ids = []
    scene_ids = []
    seen_scenes = set()
    
    # 需要跳过的场景
    skip_scenes = {}
    
    print(f"\n=== 开始读取场景文件 ===")
    print(f"文件路径: {file_path}")
    print(f"是否包含标题行: {has_header}")
    print(f"黑名单场景: {skip_scenes}\n")
    
    with open(file_path, "r") as f:
        if has_header:
            next(f)
        for line_num, line in enumerate(f, 1):
            episode_id, scene_id = line.strip().split(",")
            scene_name = scene_id.split("/")[-2]  # 提取场景名称
            print(f"[第{line_num}行] Episode ID: {episode_id}")
            print(f"         场景名称: {scene_name}")
            print(f"         完整路径: {scene_id}")
            
            if scene_name in skip_scenes:
                print(f"         状态: 跳过(黑名单场景)\n")
                continue
                
            if scene_id not in seen_scenes:
                seen_scenes.add(scene_id)
                episode_ids.append(episode_id)
                scene_ids.append(scene_id)
                print(f"         状态: 添加(新场景)\n")
            else:
                print(f"         状态: 跳过(场景已存在)\n")
    
    print("=== 场景加载统计 ===")
    print(f"总行数: {line_num}")
    print(f"有效场景数: {len(episode_ids)}")
    print(f"跳过场景数: {line_num - len(episode_ids)}")
    print("==================\n")
    return episode_ids, scene_ids


class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def main():
    # parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-type",
        default="blind",
        choices=["blind", "rgb", "depth", "rgbd"],
    )
    parser.add_argument("--model-path", default="", type=str)
    parser.add_argument(
        "--task-config", type=str, default="configs/pointnav_d_orignal.yaml"
    )
    parser.add_argument("--episodes-to-visualize-file-path", default="", type=str)
    parser.add_argument(
        "--episodes-to-visualize-file-has-header", default=False, action="store_true"
    )
    parser.add_argument("--seed-file-path", type=str, default="")
    parser.add_argument("--make-videos", default=False, action="store_true")
    parser.add_argument("--make-maps", default=False, action="store_true")
    parser.add_argument("--make-blank-maps", default=False, action="store_true")
    parser.add_argument("--map-height", type=int, default=200)
    parser.add_argument("--map-dir", type=str, default="habitat_maps/")

    args = parser.parse_args()

    # get exp config
    exp_config = get_config(args.task_config)

    # get seeds if provided; otherwise use default seed from Habitat
    seeds = []
    if args.seed_file_path != "":
        seeds = utils_files.load_seeds_from_file(args.seed_file_path)
    else:
        seeds = [exp_config.SEED]

    # get episode ID's and scene ID's of episodes to visualize (only one per scene)
    print("\n开始加载场景列表...")
    episode_ids, scene_ids = load_unique_scene_episodes(
        file_path=args.episodes_to_visualize_file_path,
        has_header=args.episodes_to_visualize_file_has_header
    )
    print("场景列表加载完成\n")

    # instantiate a discrete/continuous evaluator
    print("初始化评估器...")
    evaluator = None
    if "PHYSICS_SIMULATOR" in exp_config:
        print("使用物理模拟器")
        evaluator = HabitatEvaluator(
            config_paths=args.task_config,
            input_type=args.input_type,
            model_path=args.model_path,
            enable_physics=True,
        )
    elif "SIMULATOR" in exp_config:
        print("使用离散模拟器")
        evaluator = HabitatEvaluator(
            config_paths=args.task_config,
            input_type=args.input_type,
            model_path=args.model_path,
            enable_physics=False,
        )
    print("评估器初始化完成\n")

    # evaluate and generate videos
    if args.make_videos:
        # create video dir
        os.makedirs(name=f"{exp_config.VIDEO_DIR}", exist_ok=True)

        for seed in seeds:
            evaluator.generate_videos(episode_ids, scene_ids, seed)

    # evaluate and visualize top-down maps with agent position, shortest
    # and actual path
    if args.make_maps:
        # create map dir
        os.makedirs(name=f"{args.map_dir}", exist_ok=True)

        # create a list of per-seed maps for each episode
        maps: Dict[str, List[np.ndarray]] = {}
        for episode_id, scene_id in zip(episode_ids, scene_ids):
            maps[f"{episode_id},{scene_id}"] = []

        for seed in seeds:
            maps_one_seed = evaluator.generate_maps(
                episode_ids, scene_ids, seed, args.map_height
            )
            # add map from each episode to maps
            for episode_id, scene_id in zip(episode_ids, scene_ids):
                maps[f"{episode_id},{scene_id}"].append(
                    maps_one_seed[f"{episode_id},{scene_id}"]
                )

        # make grid of maps for each episode
        for episode_id, scene_id in zip(episode_ids, scene_ids):
            utils_visualization.generate_grid_of_maps(
                episode_id,
                scene_id,
                seeds,
                maps[f"{episode_id},{scene_id}"],
                args.map_dir,
            )

    # visualize blank top-down maps
    if args.make_blank_maps:
        print(f"\n=== 开始生成空白地图 ===")
        print(f"输出目录: {args.map_dir}")
        print(f"地图高度: {args.map_height}")
        os.makedirs(name=f"{args.map_dir}", exist_ok=True)

        print("\n正在获取空白地图...")
        blank_maps = evaluator.get_blank_maps(episode_ids, scene_ids, args.map_height)
        print(f"获取完成,共 {len(blank_maps)} 个地图")
        print("可用的地图键值:", list(blank_maps.keys())[:5], "...\n")  # 打印前5个键值作为示例

        for idx, (episode_id, scene_id) in enumerate(zip(episode_ids, scene_ids), 1):
            scene_name = scene_id.split("/")[-2]
            print(f"\n处理第 {idx}/{len(episode_ids)} 个场景")
            print(f"场景名称: {scene_name}")
            print(f"Episode ID: {episode_id}")
            print(f"场景路径: {scene_id}")
            
            # 构建地图键值
            map_key = f"{episode_id},{scene_id}"
            print(f"地图键值: {map_key}")
            
            if map_key not in blank_maps:
                print(f"× 错误: 找不到对应的地图数据")
                continue
                
            try:
                with time_limit(300):  # 5分钟超时
                    print("正在保存地图...")
                    map_data = blank_maps[map_key]
                    if map_data is None:
                        print("× 错误: 地图数据为空")
                        continue
                        
                    utils_visualization.save_blank_map(
                        episode_id,
                        scene_id,
                        map_data,
                        args.map_dir,
                    )
                    print("√ 地图保存成功")
            except TimeoutException:
                print("× 处理超时(>5分钟),跳过")
                continue
            except KeyError as e:
                print(f"× 键值错误: {str(e)}")
                continue
            except Exception as e:
                print(f"× 处理出错: {str(e)}")
                print(f"错误类型: {type(e).__name__}")
                continue
        
        print("\n=== 空白地图生成完成 ===\n")


if __name__ == "__main__":
    main()

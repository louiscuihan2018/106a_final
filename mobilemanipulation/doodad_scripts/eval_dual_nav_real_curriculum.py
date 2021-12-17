"""
Call in the root directory (i.e. ../ from the directory this file is in)
"""

import numpy as np

from softlearning.utils.dict import deep_update

from softlearning.environments.utils import get_environment_from_params
from softlearning.policies.utils import get_additional_policy_params

from softlearning import policies

from examples.dual_perturbation.variants import POLICY_PARAMS_BASE

from copy import deepcopy
import os

import pprint
import time

TELEOP = False

curriculum_checkpoints = [
    "/home/charles/ray_results/curriculum_v2_1/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_2/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_3/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_4/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_5/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_6/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_7/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_8/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_9/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_10/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_11/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_12/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_13/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_14/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_15/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_16/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_17/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_18/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_19/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_20/checkpoint_error",
    "/home/charles/ray_results/curriculum_v2_21/checkpoint_error",
]

def main():
    # env
    environment_params = {
        "universe": "gym",
        "domain": "Locobot",
        "task": "RealNavigationGraspingDualPerturbation-v0",
        "kwargs": {
            "grasp_algorithm": "soft_q_curriculum",
            "grasp_perturbation": "random_uniform",
            "grasp_perturbation_params": {
                "num_steps": 10,
            },
            "nav_perturbation": "random_uniform",
            "nav_perturbation_params": {
                "num_steps": 10,
            },
            "pause_filepath": "/home/brian/realmobile/locobot_pause",
            "add_uncertainty_bonus": False,
            "alive_penalty": 0.0,
            "is_training": False,
            'reset_free': False,
            'observation_keys': ('pixels',),
            'max_ep_len': 250,
            'grasp_algorithm_params': {
                'image_reward_eval': False,
                # 'grasp_model_name': 'sock_2000',
            },
        }
    }
    env = get_environment_from_params(environment_params)
    env.finish_init(
        algorithm=None,
        replay_pool=None,
        grasp_rnd_trainer=None,
        grasp_perturbation_algorithm=None,
        grasp_perturbation_policy=None,
        nav_rnd_trainer=None,
        nav_perturbation_algorithm=None,
        nav_perturbation_policy=None,
    )

    # policy
    policy_params = deepcopy(POLICY_PARAMS_BASE['gaussian'])
    preprocessor_params = {
        'class_name': 'convnet_preprocessor',
        'config': {
            'conv_filters': (64, 64, 64),
            'conv_kernel_sizes': (3, 3, 3),
            'conv_strides': (2, 2, 2),
            'normalization_type': None,
            'downsampling_type': 'pool',
            'activation': 'relu',
        },
    }
    pixel_keys = ('pixels',)
    preprocessors = dict()
    for key in pixel_keys:
        params = deepcopy(preprocessor_params)
        params['config']['name'] = 'convnet_preprocessor_' + key
        preprocessors[key] = params

    policy_params['config']['hidden_layer_sizes'] = (512, 512)
    policy_params['config']['preprocessors'] = preprocessors
    policy_params['config']['activation'] = 'relu'
    policy_params['config'].update({
        'input_shapes': env.observation_shape,
        'output_shape': env.action_shape,
        **get_additional_policy_params(policy_params['class_name'], env)
    })
    policy = policies.get(policy_params)

    # load
    save_path = os.path.join(curriculum_checkpoints[-1], 'policy')
    status = policy.load_weights(save_path)
    status.assert_consumed().run_restore_ops()

    # env.load("/home/brian/ray_results/real_trained_load_nag4_bonus_uniform_5/checkpoint_1")
    env.load(curriculum_checkpoints[-1])

    # input("Enter to start...")
    print("starting in 20s")
    time.sleep(20)
    print("start")

    try:
        # eval
        env.reset()
        rewards = []
        start_time = time.time()
        success_timings = []
        i = 0
        while time.time() - start_time < 60*15:  # 15 minutes for each eval
            print(i)
            i += 1
            obs = env.get_observation()
            #action = np.random.uniform(-1, 1, size=(2,))
            action = policy.action(obs).numpy()
            print(action)
            env.do_move(action)
            time.sleep(0.55)
            reward = env.do_grasp(action, {})
            print(reward)
            if reward:
                success_timings.append(time.time() - start_time)
            rewards.append(reward)
    except Exception as e:
        print(e)

    infos = {}
    #infos["rewards"] = rewards
    infos["no_respawn_eval_returns"] = sum(rewards)

    pprint.pprint(infos)
    print(rewards)
    print(success_timings)
    print('objects grasped:', len(success_timings))

main()


from copy import deepcopy

from ray import tune
import numpy as np

from softlearning.utils.git import get_git_rev
from softlearning.utils.misc import get_host_name
from softlearning.utils.dict import deep_update

DEFAULT_KEY = "__DEFAULT_KEY__"

M = 512

ALGORITHM_PARAMS_BASE = {
    'config': {
        'train_every_n_steps': 1,
        'n_train_repeat': 10,
        'eval_render_kwargs': {},
        'eval_n_episodes': 1,
        'num_warmup_samples': tune.sample_from(lambda spec: (
            # 5 * (spec.get('config', spec)
            #       ['sampler_params']
            #       ['config']
            #       ['max_path_length'])
            1000
        )),
    }
}


ALGORITHM_PARAMS_ADDITIONAL = {
    'SAC': {
        'class_name': 'SAC',
        'config': {
            'policy_lr': 3e-4,
            'Q_lr': 3e-4,
            'alpha_lr': 3e-4,
            'target_update_interval': 1,
            'tau': 5e-3,
            'target_entropy': 'auto',

            'discount': 0.99,
            'reward_scale': 1.0,
        },
    },
    'SACMixed': {
        'class_name': 'SACMixed',
        'config': {
            'policy_lr': 3e-4,
            'Q_lr': 3e-4,
            'alpha_lr': 3e-4,
            'target_update_interval': 1,
            'tau': 5e-3,
            'target_entropy': 'auto',

            'discount': 0.95,
            'reward_scale': 1.0,

            'discrete_entropy_ratio_start': 0.5,
            'discrete_entropy_ratio_end': 0.5,
            'discrete_entropy_timesteps': 60000,
        },
    },
    'SACDiscrete': {
        'class_name': 'SACDiscrete',
        'config': {
            'policy_lr': 3e-4,
            'Q_lr': 3e-4,
            'alpha_lr': 3e-4,
            'target_update_interval': 1,
            'tau': 5e-3,

            'discount': 0.95,
            'reward_scale': 1.0,

            'target_entropy_start': 'auto',
            'entropy_ratio_start': 0.9,
            'entropy_ratio_end': 0.55,
            'entropy_timesteps': 60000,
        },
    },
    'SQL': {
        'class_name': 'SQL',
        'config': {
            'policy_lr': 3e-4,
            'target_update_interval': 1,
            'discount': 0.99,
            'tau': 5e-3,
            'reward_scale': tune.sample_from(lambda spec: (
                {
                    'Swimmer': 30,
                    'Hopper': 30,
                    'HalfCheetah': 30,
                    'Walker2d': 10,
                    'Ant': 300,
                    'Humanoid': 100,
                    'Pendulum': 1,
                }.get(
                    spec.get('config', spec)
                    ['environment_params']
                    ['training']
                    ['domain'],
                    1.0
                ),
            )),
        },
    },
}


POLICY_PARAMS_BASE = {
    'gaussian': {
        'class_name': 'FeedforwardGaussianPolicy',
        'config': {
            'hidden_layer_sizes': (M, M),
            'squash': True,
            'observation_keys': None,
            'preprocessors': None,
        },
    },
    'discrete_gaussian': {
        'class_name': 'FeedforwardDiscreteGaussianPolicy',
        'config': {
            'hidden_layer_sizes': (M, M),
            'observation_keys': None,
            'preprocessors': None,
        },
    },
    'discrete': {
        'class_name': 'FeedforwardDiscretePolicy',
        'config': {
            'hidden_layer_sizes': (M, M),
            'observation_keys': None,
            'preprocessors': None,
        },
    },
}

TOTAL_STEPS_PER_UNIVERSE_DOMAIN_TASK = {
    DEFAULT_KEY: int(1e4),
    'gym': {
        DEFAULT_KEY: int(1e4),
        'Swimmer': {
            DEFAULT_KEY: int(1e5),
            'v3': int(5e5),
        },
        'Hopper': {
            DEFAULT_KEY: int(5e6),
            'v3': int(5e6),
        },
        'HalfCheetah': {
            DEFAULT_KEY: int(3e6),
            'v3': int(3e6),
        },
        'Walker2d': {
            DEFAULT_KEY: int(5e6),
            'v3': int(5e6),
        },
        'Ant': {
            DEFAULT_KEY: int(3e6),
            'v3': int(3e6),
        },
        'Humanoid': {
            DEFAULT_KEY: int(3e6),
            'Stand-v3': int(1e8),
            'SimpleStand-v3': int(1e8),
            'v3': int(1e8),
        },
        'Pendulum': {
            DEFAULT_KEY: int(1e4),
            'v3': int(1e4),
        },
        'Point2DEnv': {
            DEFAULT_KEY: int(5e4),
        },
        'Locobot': {
            DEFAULT_KEY: int(2e5),
            'ImageNavigation-v0': int(1e6),
            'MixedNavigation-v0': int(1e5),
            'MixedNavigationReach-v0': int(1e6),
            'ImageNavigationResetFree-v0': int(1e6),
            'MixedNavigationResetFree-v0': int(1e5),
            'NavigationVacuum-v0': int(1e6),
            'NavigationVacuumResetFree-v0': int(2e5),
            'NavigationDQNGrasping-v0': int(1e5),
            'DiscreteGrasping-v0': int(1e5),
            'ContinuousMultistepGrasping-v0': int(1e6),
        },
        'Tests': {
            DEFAULT_KEY: int(1e5),
            'LineReach-v0': int(1e5),
            'LineGrasping-v0': int(1e5),
            'LineGraspingDiscrete-v0': int(1e5),
            'PointGridExploration-v0': int(1e5),
        },
    },
    'dm_control': {
        # BENCHMARKING
        DEFAULT_KEY: int(3e6),
        'acrobot': {
            DEFAULT_KEY: int(3e6),
            # 'swingup': int(None),
            # 'swingup_sparse': int(None),
        },
        'ball_in_cup': {
            DEFAULT_KEY: int(3e6),
            # 'catch': int(None),
        },
        'cartpole': {
            DEFAULT_KEY: int(3e6),
            # 'balance': int(None),
            # 'balance_sparse': int(None),
            # 'swingup': int(None),
            # 'swingup_sparse': int(None),
            # 'three_poles': int(None),
            # 'two_poles': int(None),
        },
        'cheetah': {
            DEFAULT_KEY: int(3e6),
            'run': int(1e7),
        },
        'finger': {
            DEFAULT_KEY: int(3e6),
            # 'spin': int(None),
            # 'turn_easy': int(None),
            # 'turn_hard': int(None),
        },
        'fish': {
            DEFAULT_KEY: int(3e6),
            # 'upright': int(None),
            # 'swim': int(None),
        },
        'hopper': {
            DEFAULT_KEY: int(3e6),
            # 'stand': int(None),
            'hop': int(1e7),
        },
        'humanoid': {
            DEFAULT_KEY: int(1e7),
            'stand': int(1e7),
            'walk': int(1e7),
            'run': int(1e7),
            # 'run_pure_state': int(1e7),
        },
        'manipulator': {
            DEFAULT_KEY: int(3e6),
            'bring_ball': int(1e7),
            # 'bring_peg': int(None),
            # 'insert_ball': int(None),
            # 'insert_peg': int(None),
        },
        'pendulum': {
            DEFAULT_KEY: int(3e6),
            # 'swingup': int(None),
        },
        'point_mass': {
            DEFAULT_KEY: int(3e6),
            # 'easy': int(None),
            # 'hard': int(None),
        },
        'reacher': {
            DEFAULT_KEY: int(3e6),
            # 'easy': int(None),
            # 'hard': int(None),
        },
        'swimmer': {
            DEFAULT_KEY: int(3e6),
            # 'swimmer6': int(None),
            # 'swimmer15': int(None),
        },
        'walker': {
            DEFAULT_KEY: int(3e6),
            # 'stand': int(None),
            'walk': int(1e7),
            'run': int(1e7),
        },
        # EXTRA
        'humanoid_CMU': {
            DEFAULT_KEY: int(3e6),
            'run': int(1e7),
            # 'stand': int(None),
        },
        'quadruped': {
            DEFAULT_KEY: int(3e6),
            'run': int(1e7),
            'walk': int(1e7),
        },
    },
}


MAX_PATH_LENGTH_PER_UNIVERSE_DOMAIN_TASK = {
    DEFAULT_KEY: 1000,
    'gym': {
        DEFAULT_KEY: 1000,
        'Point2DEnv': {
            DEFAULT_KEY: 50,
        },
        'Pendulum': {
            DEFAULT_KEY: 200,
        },
        'Locobot': {
            DEFAULT_KEY: 200,
            'ImageMultiGrasping-v0': 1,
            'ImageSingleGrasping-v0': 1,
            'ImageNavigation-v0': 200,
            'MixedNavigation-v0': 200,
            'MixedNavigationReach-v0': 100,
            'ImageNavigationResetFree-v0': 200,
            'MixedNavigationResetFree-v0': 200,
            'NavigationVacuum-v0': 200,
            'NavigationVacuumResetFree-v0': 200,
            'NavigationDQNGrasping-v0': 200,
            'DiscreteGrasping-v0': 1,
            'ContinuousMultistepGrasping-v0': 15,
        },
        'Tests': {
            DEFAULT_KEY: 100,
            'LineReach-v0': 100,
            'LineGrasping-v0': 1,
            'LineGraspingDiscrete-v0': 1,
            'PointGridExploration-v0': 20,
        },
    },
}

EPOCH_LENGTH_PER_UNIVERSE_DOMAIN_TASK = {
    DEFAULT_KEY: 1000,
    'gym': {
        DEFAULT_KEY: 1000,
        'Locobot': {
            DEFAULT_KEY: 1000,
            'MixedNavigation-v0': 1000,
            'ImageNavigationResetFree-v0': 1000,
            'MixedNavigationResetFree-v0': 1000,
            'NavigationVacuum-v0': 1000,
            'NavigationVacuumResetFree-v0': 1000,
            'NavigationDQNGrasping-v0': 1000,
            'DiscreteGrasping-v0': 1000,
            'ContinuousMultistepGrasping-v0': 1000,
        },
        'Tests': {
            DEFAULT_KEY: 1000,
            'LineReach-v0': 1000,
            'LineGrasping-v0': 1000,
            'LineGraspingDiscrete-v0': 1000,
            'PointGridExploration-v0': 1000,
        },
    },
}


ENVIRONMENT_PARAMS_PER_UNIVERSE_DOMAIN_TASK = {
    'gym': {
        'Swimmer': {  # 2 DoF
        },
        'Hopper': {  # 3 DoF
        },
        'HalfCheetah': {  # 6 DoF
        },
        'Walker2d': {  # 6 DoF
        },
        'Ant': {  # 8 DoF
            'Parameterizable-v3': {
                'healthy_reward': 0.0,
                'healthy_z_range': (-np.inf, np.inf),
                'exclude_current_positions_from_observation': False,
            }
        },
        'Humanoid': {  # 17 DoF
            'Parameterizable-v3': {
                'healthy_reward': 0.0,
                'healthy_z_range': (-np.inf, np.inf),
                'exclude_current_positions_from_observation': False,
            }
        },
        'Pusher2d': {  # 3 DoF
            'Default-v3': {
                'arm_object_distance_cost_coeff': 0.0,
                'goal_object_distance_cost_coeff': 1.0,
                'goal': (0, -1),
            },
            'DefaultReach-v0': {
                'arm_goal_distance_cost_coeff': 1.0,
                'arm_object_distance_cost_coeff': 0.0,
            },
            'ImageDefault-v0': {
                'image_shape': (32, 32, 3),
                'arm_object_distance_cost_coeff': 0.0,
                'goal_object_distance_cost_coeff': 3.0,
            },
            'ImageReach-v0': {
                'image_shape': (32, 32, 3),
                'arm_goal_distance_cost_coeff': 1.0,
                'arm_object_distance_cost_coeff': 0.0,
            },
            'BlindReach-v0': {
                'image_shape': (32, 32, 3),
                'arm_goal_distance_cost_coeff': 1.0,
                'arm_object_distance_cost_coeff': 0.0,
            }
        },
        'Point2DEnv': {
            'Default-v0': {
                'observation_keys': ('observation', 'desired_goal'),
            },
            'Wall-v0': {
                'observation_keys': ('observation', 'desired_goal'),
            },
        },
        'Sawyer': {
            task_name: {
                'has_renderer': False,
                'has_offscreen_renderer': False,
                'use_camera_obs': False,
                'reward_shaping': tune.grid_search([True, False]),
            }
            for task_name in (
                    'Lift',
                    'NutAssembly',
                    'NutAssemblyRound',
                    'NutAssemblySingle',
                    'NutAssemblySquare',
                    'PickPlace',
                    'PickPlaceBread',
                    'PickPlaceCan',
                    'PickPlaceCereal',
                    'PickPlaceMilk',
                    'PickPlaceSingle',
                    'Stack',
            )
        },
        'Locobot': {
            'ImageGrasping-v0': {
                'pixel_wrapper_kwargs': {
                    'observation_key': 'pixels',
                    'pixels_only': True,
                    'render_kwargs': {
                    },
                },
            },
            'ImageMultiGrasping-v0': {
                'pixel_wrapper_kwargs': {
                    'observation_key': 'pixels',
                    'pixels_only': True,
                    'render_kwargs': {
                    },
                },
            },
            'ImageSingleGrasping-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': True,
                    'render_kwargs': {},
                },

                'random_orientation': False,
                'action_dim': 2,
                'min_blocks': 1,
                'max_blocks': 6,
                'crop_output': True,
                'min_other_blocks': 0,
                'max_other_blocks': 6
            },
            'MixedNavigationReach-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': False,
                },
                'observation_keys': ('current_velocity', 'target_velocity', 'pixels'),
                'room_name': 'simple',
                'room_params': {
                    'num_objects': 20, 
                    'object_name': "greensquareball", 
                    'wall_size': 3.0, 
                    'no_spawn_radius': 0.6,
                },
                'max_ep_len': 100,
                'image_size': 100,
                'steps_per_second': 2,
                'max_velocity': 20.0,
                'max_acceleration': 4.0
            },
            'ImageNavigation-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': True,
                },
                # 'room_name': 'simple_obstacles',
                # 'room_params': {
                #     'num_objects': 100, 
                #     'object_name': "greensquareball", 
                #     'wall_size': 5.0, 
                # },
                'room_name': 'medium',
                'room_params': {
                    'num_objects': 100, 
                    'object_name': "greensquareball", 
                    'no_spawn_radius': 0.8,
                },
                'max_ep_len': 200,
                'image_size': 100,
            },
            'ImageNavigationResetFree-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': True,
                },
                'reset_free': True,
                'room_name': 'medium',
                'room_params': {
                    'num_objects': 100, 
                    'object_name': "greensquareball", 
                    'no_spawn_radius': 0.8,
                },
                'max_ep_len': float('inf'),
                'image_size': 100,
            },
            'MixedNavigation-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': False,
                },
                'observation_keys': ('current_velocity', 'pixels'),
                # 'room_name': 'simple',
                # 'room_params': {
                #     'num_objects': 80, 
                #     'object_name': "greensquareball", 
                #     'wall_size': 5.0, 
                #     'no_spawn_radius': 0.8,
                # },
                'room_name': 'medium',
                'room_params': {
                    'num_objects': 200, 
                    'object_name': "greensquareball", 
                    'no_spawn_radius': 0.7,
                    'wall_size': 7.0
                },
                'max_ep_len': 200,
                'image_size': 100,
                'steps_per_second': 2,
                'max_velocity': 20.0,
                'max_acceleration': 4.0
            },
            'MixedNavigationResetFree-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': False,
                },
                'observation_keys': ('current_velocity', 'target_velocity', 'pixels'),
                'reset_free': True,
                'room_name': 'medium',
                'room_params': {
                    'num_objects': 200, 
                    'object_name': "greensquareball", 
                    'no_spawn_radius': 0.7,
                    'wall_size': 7.0
                },
                'max_ep_len': float('inf'),
                'image_size': 100,
                'steps_per_second': 2,
                'max_velocity': 20.0,
                'max_acceleration': 4.0,
                'trajectory_log_dir': '/home/charlesjsun/mobilemanipulation-tf2/nohup_output/mixed_nav_rf_sac_newton5_2_traj/', 
                'trajectory_log_freq': 1000
            },
            'NavigationVacuum-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': False,
                },
                'room_name': 'simple',
                'room_params': {
                    'num_objects': 100, 
                    'object_name': "greensquareball", 
                    'no_spawn_radius': 0.55, #0.8,
                    'wall_size': 5.0
                },
                'max_ep_len': 200,
                'image_size': 100,
                'steps_per_second': 2,
                'max_velocity': 20.0,
                'max_acceleration': 4.0
            },
            'NavigationVacuumResetFree-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': False,
                },
                'reset_free': True,
                'room_name': 'simple_texture',
                'room_params': {
                    'num_objects': 100, 
                    'object_name': "greensquareball", 
                    'no_spawn_radius': 0.4, #0.55, #0.8,
                    'wall_size': 5.0
                },
                'replace_grasped_object': True,
                'max_ep_len': float('inf'),
                'image_size': 100,
                'steps_per_second': 2,
                'max_velocity': 20.0,
                'trajectory_log_dir': '/home/externalhardrive/RAIL/mobilemanipulation/nohup_output/nav_vac_no_pert_no_drop_traj/', 
                'trajectory_log_freq': 1000,
                'renders': False,
                'step_duration': 0.0,
            },
            'NavigationDQNGrasping-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': False,
                },
                'room_name': 'simple_texture',
                'room_params': {
                    'num_objects': 100, 
                    'object_name': "greensquareball", 
                    'no_spawn_radius': 0.55, #0.8,
                    'wall_size': 5.0
                },
                'is_training': True,
                'renders': False,
                'step_duration': 0.000,
                # use default everything else
            },
            'DiscreteGrasping-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': True,
                },
            },
            'ContinuousMultistepGrasping-v0': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': False,
                    'pixel_keys': ('left_camera', 'right_camera'),
                    'render_kwargs': {
                        'left_camera': {
                            'use_aux': True,
                        },
                        'right_camera': {
                            'use_aux': False,
                        },
                    },
                },
                # 'renders': True,
            },
            'RealNavigation-v0': {
                'pixel_wrapper_kwargs': {
                    #'observation_key': 'pixels',
                    'pixels_only': True,
                    'render_kwargs': {
                    },
                },
            },
            'RealGrasping-v0': {
                'pixel_wrapper_kwargs': {
                    #'observation_key': 'pixels',
                    'pixels_only': True,
                    'render_kwargs': {
                    },
                },
            },
            'RealOdomNav-v0': {
                'pixel_wrapper_kwargs': {
                    #'observation_key': 'pixels',
                    'pixels_only': True,
                    'render_kwargs': {
                    },
                },
            },
            'RealARTagNav-v0': {
                # 'pixel_wrapper_kwargs': {
                    #'observation_key': 'pixels',
                    # 'pixels_only': True,
                    # 'render_kwargs': {
                    # },
                # },
            },
        },
        'Tests': {
            'LineReach-v0': {
                'max_pos': 10.0, 
                'max_step': 1.0, 
                'collect_radius': 0.1,
                'max_ep_len': 100
            },
            'LineGrasping-v0': {
                'line_width': 32,
                'min_objects': 1,
                'max_objects': 5,
                'num_repeat': 10,
                'collect_radius': 0.03,
            },
            'LineGraspingDiscrete-v0': {
                'line_width': 32,
                'min_objects': 1,
                'max_objects': 5,
                'num_repeat': 10,
            },
            'PointGridExploration-v0': {
                'is_training': True,
                'max_steps': 20,
                'trajectory_log_freq': 100,
                'trajectory_log_dir': '/home/externalhardrive/RAIL/mobilemanipulation/nohup_output/test_point_grid_exploration_edison_21_traj/', 
            },
        },
    },
    'dm_control': {
        'ball_in_cup': {
            'catch': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': True,
                    'render_kwargs': {
                        'width': 84,
                        'height': 84,
                        'camera_id': 0,
                    },
                },
            },
        },
        'cheetah': {
            'run': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': True,
                    'render_kwargs': {
                        'width': 84,
                        'height': 84,
                        'camera_id': 0,
                    },
                },
            },
        },
        'finger': {
            'spin': {
                'pixel_wrapper_kwargs': {
                    'pixels_only': True,
                    'render_kwargs': {
                        'width': 84,
                        'height': 84,
                        'camera_id': 0,
                    },
                },
            },
        },
    },
}

EXTRA_EVALUATION_ENVIRONMENT_PARAMS_PER_UNIVERSE_DOMAIN_TASK = {
    'gym': {
        'Locobot': {
            'ImageNavigationResetFree-v0': {
                'reset_free': False,
                'max_ep_len': 200,
            },
            'MixedNavigationResetFree-v0': {
                'reset_free': False,
                'max_ep_len': 200,
                'trajectory_log_dir': None, 
                'trajectory_log_freq': 0
            },
            'NavigationVacuumResetFree-v0': {
                'reset_free': False,
                'max_ep_len': 200,
                'replace_grasped_object': False,
                'trajectory_log_dir': None, 
                'trajectory_log_freq': 0,
                'renders': False,
                'step_duration': 0.0,
            },
            'NavigationDQNGrasping-v0': {
                'is_training': False,
                'renders': False,
                'step_duration': 0.000,
            },
            'ContinuousMultistepGrasping-v0': {
                'renders': False,
            },
        },
        'Tests': {
            'PointGridExploration-v0': {
                'is_training': False,
                'trajectory_log_dir': None,
                'trajectory_log_freq': 0,
            },
        }
    },
}

def get_epoch_length(universe, domain, task):
    level_result = EPOCH_LENGTH_PER_UNIVERSE_DOMAIN_TASK.copy()
    for level_key in (universe, domain, task):
        if isinstance(level_result, int):
            return level_result

        level_result = level_result.get(level_key) or level_result[DEFAULT_KEY]

    return level_result


def get_max_path_length(universe, domain, task):
    level_result = MAX_PATH_LENGTH_PER_UNIVERSE_DOMAIN_TASK.copy()
    for level_key in (universe, domain, task):
        if isinstance(level_result, int):
            return level_result

        level_result = level_result.get(level_key) or level_result[DEFAULT_KEY]

    return level_result


def get_checkpoint_frequency(spec):
    num_checkpoints = 10
    config = spec.get('config', spec)
    checkpoint_frequency = (
        config
        ['algorithm_params']
        ['config']
        ['n_epochs']
    ) // num_checkpoints

    return checkpoint_frequency


def get_total_timesteps(universe, domain, task):
    level_result = TOTAL_STEPS_PER_UNIVERSE_DOMAIN_TASK.copy()
    for level_key in (universe, domain, task):
        if isinstance(level_result, (int, float)):
            return level_result

        level_result = (
            level_result.get(level_key)
            or level_result[DEFAULT_KEY])

    return level_result


def get_algorithm_params(universe, domain, task):
    total_timesteps = get_total_timesteps(universe, domain, task)
    epoch_length = get_epoch_length(universe, domain, task)
    n_epochs = total_timesteps / epoch_length
    assert n_epochs == int(n_epochs)
    algorithm_params = {
        'config': {
            'n_epochs': int(n_epochs),
            'epoch_length': epoch_length,
            'min_pool_size': get_max_path_length(universe, domain, task),
            'batch_size': 256,
        }
    }

    return algorithm_params


def get_environment_params(universe, domain, task):
    environment_params = (
        ENVIRONMENT_PARAMS_PER_UNIVERSE_DOMAIN_TASK
        .get(universe, {}).get(domain, {}).get(task, {}))

    return environment_params

def get_evaluation_environment_params(universe, domain, task):
    environment_params = deepcopy(get_environment_params(universe, domain, task))
    extra_params = (
        EXTRA_EVALUATION_ENVIRONMENT_PARAMS_PER_UNIVERSE_DOMAIN_TASK
        .get(universe, {}).get(domain, {}).get(task, {}))
    
    environment_params.update(extra_params)
    return environment_params


def get_variant_spec_base(universe, domain, task, policy, algorithm):
    algorithm_params = deep_update(
        deepcopy(ALGORITHM_PARAMS_BASE),
        deepcopy(ALGORITHM_PARAMS_ADDITIONAL.get(algorithm, {})),
        deepcopy(get_algorithm_params(universe, domain, task)),
    )

    policy_params = deepcopy(POLICY_PARAMS_BASE[policy])
    
    # policy_params = deep_update(
    #     policy_params,
    #     deepcopy(
    #         EXTRA_POLICY_PARAMS_PER_UNIVERSE_DOMAIN_TASK
    #         .get(universe, {}).get(domain, {}).get(task, {}))
    # )

    variant_spec = {
        'git_sha': get_git_rev(__file__),

        'environment_params': {
            'training': {
                'domain': domain,
                'task': task,
                'universe': universe,
                'kwargs': get_environment_params(universe, domain, task),
            },
            'evaluation': {
                'domain': domain,
                'task': task,
                'universe': universe,
                'kwargs': get_evaluation_environment_params(universe, domain, task),
            },
        },
        # 'policy_params': tune.sample_from(get_policy_params),
        'policy_params': policy_params,
        # 'exploration_policy_params': {
        #     'class_name': 'ContinuousUniformPolicy',
        #     'config': {
        #         'observation_keys': tune.sample_from(lambda spec: (
        #             spec.get('config', spec)
        #             ['policy_params']
        #             ['config']
        #             .get('observation_keys')
        #         ))
        #     },
        # },
        'Q_params': {
            'class_name': 'double_feedforward_Q_function',
            'config': {
                'hidden_layer_sizes': (M, M),
                'observation_keys': None,
                'preprocessors': None,
            },
        },
        'algorithm_params': algorithm_params,
        'replay_pool_params': {
            'class_name': 'SimpleReplayPool',
            'config': {
                'max_size': int(1e5),
            },
        },
        'sampler_params': {
            'class_name': 'SimpleSampler',
            'config': {
                'max_path_length': get_max_path_length(universe, domain, task),
            }
        },
        'run_params': {
            'host_name': get_host_name(),
            'seed': tune.sample_from(lambda spec: np.random.randint(0, 10000)),
            'checkpoint_at_end': True,
            'checkpoint_frequency': tune.sample_from(get_checkpoint_frequency),
            'checkpoint_replay_pool': False,
        },
    }

    return variant_spec


def is_image_env(universe, domain, task, variant_spec):
    return 'pixel_wrapper_kwargs' in variant_spec['environment_params']['training']['kwargs']


def get_variant_spec_image(universe,
                           domain,
                           task,
                           policy,
                           algorithm,
                           *args,
                           **kwargs):
    variant_spec = get_variant_spec_base(
        universe, domain, task, policy, algorithm, *args, **kwargs)

    if is_image_env(universe, domain, task, variant_spec):

        preprocessor_params = {
            'class_name': 'convnet_preprocessor',
            'config': {
                'conv_filters': (64, 64, 64),
                'conv_kernel_sizes': (3, 3, 3),
                'conv_strides': (2, 2, 2),
                'normalization_type': None,
                'downsampling_type': 'conv',
            },
        }

        variant_spec['policy_params']['config']['hidden_layer_sizes'] = (M, M)
        pixel_keys = variant_spec['environment_params']['training']['kwargs']['pixel_wrapper_kwargs'].get(
            'pixel_keys', ('pixels',))
        
        preprocessors = dict()
        for key in pixel_keys:
            params = deepcopy(preprocessor_params)
            params['config']['name'] = 'convnet_preprocessor_' + key
            preprocessors[key] = params

        variant_spec['policy_params']['config']['preprocessors'] = preprocessors
    
        variant_spec['Q_params']['config']['hidden_layer_sizes'] = (
            tune.sample_from(lambda spec: (deepcopy(
                spec.get('config', spec)
                ['policy_params']
                ['config']
                ['hidden_layer_sizes']
            )))
        )
        variant_spec['Q_params']['config']['preprocessors'] = tune.sample_from(
            lambda spec: (
                deepcopy(
                    spec.get('config', spec)
                    ['policy_params']
                    ['config']
                    ['preprocessors']),
                None,  # Action preprocessor is None
            ))

    return variant_spec


def get_variant_spec(args):
    universe, domain, task = args.universe, args.domain, args.task

    variant_spec = get_variant_spec_image(
        universe, domain, task, args.policy, args.algorithm)

    if args.checkpoint_replay_pool is not None:
        variant_spec['run_params']['checkpoint_replay_pool'] = (
            args.checkpoint_replay_pool)

    return variant_spec

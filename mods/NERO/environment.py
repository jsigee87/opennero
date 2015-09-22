import copy
import math
import random

import common
import constants
import module
import OpenNero

class NeroEnvironment(OpenNero.Environment):
    """
    Environment for the Nero
    """
    def __init__(self):
        """
        Create the environment
        """
        OpenNero.Environment.__init__(self)

        self.flag_loc = None
        self.flag_id = None

        self.lifetime = constants.DEFAULT_LIFETIME
        self.hitpoints = constants.DEFAULT_HITPOINTS

        x = constants.XDIM / 2.0
        y = constants.YDIM / 3.0
        self.spawn_x = {
            constants.OBJECT_TYPE_TEAM_0: x,
            constants.OBJECT_TYPE_TEAM_1: x
        }
        self.spawn_y = {
            constants.OBJECT_TYPE_TEAM_0: y,
            constants.OBJECT_TYPE_TEAM_1: 2 * y
        }
        self.reward_weights = dict((f, 0.) for f in constants.FITNESS_DIMENSIONS)
        
    def setup(self):
        # world walls
        height = constants.HEIGHT + constants.OFFSET
        common.addObject(
            "data/shapes/cube/Cube.xml",
            OpenNero.Vector3f(constants.XDIM/2, 0, height),
            OpenNero.Vector3f(0, 0, 90),
            scale=OpenNero.Vector3f(constants.WIDTH, constants.XDIM, constants.HEIGHT*2),
            label="World Wall0",
            type=constants.OBJECT_TYPE_OBSTACLE)
        common.addObject(
            "data/shapes/cube/Cube.xml",
            OpenNero.Vector3f(0, constants.YDIM/2, height),
            OpenNero.Vector3f(0, 0, 0),
            scale=OpenNero.Vector3f(constants.WIDTH, constants.YDIM, constants.HEIGHT*2),
            label="World Wall1",
            type=constants.OBJECT_TYPE_OBSTACLE)
        common.addObject(
            "data/shapes/cube/Cube.xml",
            OpenNero.Vector3f(constants.XDIM, constants.YDIM/2, height),
            OpenNero.Vector3f(0, 0, 0),
            scale=OpenNero.Vector3f(constants.WIDTH, constants.YDIM, constants.HEIGHT*2),
            label="World Wall2",
            type=constants.OBJECT_TYPE_OBSTACLE)
        common.addObject(
            "data/shapes/cube/Cube.xml",
            OpenNero.Vector3f(constants.XDIM/2, constants.YDIM, height),
            OpenNero.Vector3f(0, 0, 90),
            scale=OpenNero.Vector3f(constants.WIDTH, constants.XDIM, constants.HEIGHT*2),
            label="World Wall3",
            type=constants.OBJECT_TYPE_OBSTACLE)

        # Add an obstacle wall in the middle
        common.addObject(
            "data/shapes/cube/Cube.xml",
            OpenNero.Vector3f(constants.XDIM/2, constants.YDIM/2, height),
            OpenNero.Vector3f(0, 0, 90),
            scale=OpenNero.Vector3f(constants.WIDTH, constants.YDIM / 4, constants.HEIGHT*2),
            label="World Wall4",
            type=constants.OBJECT_TYPE_OBSTACLE)

        # Add some trees
        for i in (0.25, 0.75):
            for j in (0.25, 0.75):
                # don't collide with trees - they are over 500 triangles each
                common.addObject(
                    "data/shapes/tree/Tree.xml",
                    OpenNero.Vector3f(i * constants.XDIM, j * constants.YDIM, constants.OFFSET),
                    OpenNero.Vector3f(0, 0, 0),
                    scale=OpenNero.Vector3f(1, 1, 1),
                    label="Tree %d %d" % (10 * i, 10 * j),
                    type=constants.OBJECT_TYPE_LEVEL_GEOM)
                # collide with their trunks represented with cubes instead
                common.addObject(
                    "data/shapes/cube/Cube.xml",
                    OpenNero.Vector3f(i * constants.XDIM, j * constants.YDIM, constants.OFFSET),
                    OpenNero.Vector3f(0,0,0),
                    scale=OpenNero.Vector3f(1,1,constants.HEIGHT),
                    type=constants.OBJECT_TYPE_OBSTACLE)

        # Add the surrounding Environment
        common.addObject(
            "data/terrain/NeroWorld.xml",
            OpenNero.Vector3f(constants.XDIM/2, constants.YDIM/2, 0),
            scale=OpenNero.Vector3f(1.2, 1.2, 1.2),
            label="NeroWorld",
            type=constants.OBJECT_TYPE_LEVEL_GEOM)

    def remove_flag(self):
        if self.flag_id:
            common.removeObject(self.flag_id)

    def set_weight(self, key, value):
        self.reward_weights[key] = value

    def change_flag(self, loc):
        if self.flag_id:
            common.removeObject(self.flag_id)
        self.flag_loc = OpenNero.Vector3f(*loc)
        self.flag_id = common.addObject(
            "data/shapes/cube/BlueCube.xml",
            self.flag_loc,
            label="Flag",
            scale=OpenNero.Vector3f(1, 1, 10),
            type=constants.OBJECT_TYPE_FLAG)

    def place_basic_turret(self, loc):
        return common.addObject(
            "data/shapes/character/steve_basic_turret.xml",
            OpenNero.Vector3f(*loc),
            type=constants.OBJECT_TYPE_TEAM_1)


    def reset(self, agent):
        """
        reset the environment to its initial state
        """
        state = agent.mod_state
        state.total_damage = 0
        state.curr_damage = 0
        if agent.group == "Agent":
            state.randomize()
            agent.state.position = copy.copy(state.initial_position)
            agent.state.rotation = copy.copy(state.initial_rotation)
            agent.teleport()
        return True

    def get_agent_info(self, agent):
        """
        return a blueprint for a new agent
        """
        for a in constants.WALL_RAY_SENSORS:
            agent.add_sensor(OpenNero.RaySensor(
                    math.cos(math.radians(a)), math.sin(math.radians(a)), 0,
                    constants.WALL_SENSOR_RADIUS,
                    constants.OBJECT_TYPE_OBSTACLE,
                    False))
        for a0, a1 in constants.FLAG_RADAR_SENSORS:
            agent.add_sensor(OpenNero.RadarSensor(
                    a0, a1, -90, 90, constants.MAX_VISION_RADIUS,
                    constants.OBJECT_TYPE_FLAG,
                    False))
        sense = constants.OBJECT_TYPE_TEAM_0
        if agent.get_team() == sense:
            sense = constants.OBJECT_TYPE_TEAM_1
        for a0, a1 in constants.ENEMY_RADAR_SENSORS:
            agent.add_sensor(OpenNero.RadarSensor(
                    a0, a1, -90, 90, constants.MAX_VISION_RADIUS,
                    sense,
                    False))
        for a in constants.TARGETING_SENSORS:
            agent.add_sensor(OpenNero.RaySensor(
                    math.cos(math.radians(a)), math.sin(math.radians(a)), 0,
                    constants.TARGET_SENSOR_RADIUS,
                    sense,
                    False))

        return agent.info

    def target(self, agent):
        """
        Returns the nearest foe in a 2-degree cone from an agent.
        """
        friends, foes = module.getMod().get_friend_foe(agent)
        if not foes:
            return None
        pose = agent.mod_state.pose
        min_f = None
        min_v = None
        for f in foes:
            p = g.mod_state.pose
            fd = self.distance(pose, p)
            fh = abs(self.angle(pose, p))
            if fh <= 2:
                v = fd / math.cos(math.radians(fh * 20))
                if min_v is None or v < min_v:
                    min_f = f
                    min_v = v
        return min_f

    def closest_enemy(self, agent):
        """
        Returns the nearest enemy to agent 
        """
        friends, foes = module.getMod().get_friend_foe(agent)
        if not foes:
            return None

        min_enemy = None
        min_dist = constants.MAX_FIRE_ACTION_RADIUS
        pose = agent.mod_state.pose
        color = OpenNero.Color(128, 0, 0, 0)
        for f in foes:
            f_pose = g.mod_state.pose
            dist = self.distance(pose, f_pose)
            if dist < min_dist:
                source_pos = agent.state.position
                enemy_pos = f.state.position
                source_pos.z = source_pos.z + 5
                enemy_pos.z = enemy_pos.z + 5
                obstacles = OpenNero.getSimContext().findInRay(
                    source_pos,
                    enemy_pos,
                    constants.OBJECT_TYPE_OBSTACLE,
                    False,
                    color,
                    color)
                if len(obstacles) == 0:
                    min_enemy = f
                    min_dist = dist
        return min_enemy

    def step(self, agent, action):
        """
        2A step for an agent
        """
        state = agent.mod_state

        #Initilize Agent state
        if agent.step == 0 and agent.group != "Turret":
            p = agent.state.position
            r = agent.state.rotation
            if agent.group == "Agent":
                r.z = random.randrange(360)
                agent.state.rotation = r
            state.reset_pose(p, r)
            return agent.info.reward.get_instance()

        # display agent info if neccessary
        if hasattr(agent, 'set_display_hint'):
            agent.set_display_hint()

        # get the desired action of the agent
        move_by = action[constants.ACTION_INDEX_SPEED]
        turn_by = math.degrees(action[constants.ACTION_INDEX_TURN])
        firing = action[constants.ACTION_INDEX_FIRE]
        firing_status = (firing >= 0.5)

        scored_hit = False
        # firing decision
        closest_enemy = self.closest_enemy(agent)
        if firing_status:
            if closest_enemy is not None:
                pose = state.pose
                closest_enemy_pose = closest_enemy.mod_state.pose
                relative_angle = self.angle(pose, closest_enemy_pose)
                if abs(relative_angle) <= 2:
                    source_pos = agent.state.position
                    closest_enemy_pos = closest_enemy.state.position
                    source_pos.z = source_pos.z + 5
                    closest_enemy_pos.z = closest_enemy_pos.z + 5
                    dist = closest_enemy_pos.getDistanceFrom(source_pos)
                    d = (constants.MAX_SHOT_RADIUS - dist)/constants.MAX_SHOT_RADIUS
                    if random.random() < d/2: # attempt a shot depending on distance
                        team_color = constants.TEAM_LABELS[agent.get_team()]
                        if team_color == 'red':
                            color = OpenNero.Color(255, 255, 0, 0)
                        elif team_color == 'blue':
                            color = OpenNero.Color(255, 0, 0, 255)
                        else:
                            color = OpenNero.Color(255, 255, 255, 0)
                        wall_color = OpenNero.Color(128, 0, 255, 0)
                        obstacles = OpenNero.getSimContext().findInRay(
                            source_pos,
                            closest_enemy_pos,
                            constants.OBJECT_TYPE_OBSTACLE,
                            True,
                            wall_color,
                            color)
                        #if len(obstacles) == 0 and random.random() < d/2:
                        if len(obstacles) == 0:
                            # count as hit depending on distance
                            closest_enemy.mod_state.curr_damage += 1
                            scored_hit = True
                else: # turn toward the enemy
                    turn_by = relative_angle

        # set animation speed
        # TODO: move constants into constants.py
        self.set_animation(agent, state, 'run')
        delay = OpenNero.getSimContext().delay
        agent.state.animation_speed = move_by * constants.ANIMATION_RATE

        reward = self.calculate_reward(agent, action, scored_hit)

        # tell the system to make the calculated motion
        # if the motion doesn't result in a collision
        dist = constants.MAX_MOVEMENT_SPEED * move_by
        heading = common.wrap_degrees(agent.state.rotation.z, turn_by)
        x = agent.state.position.x + dist * math.cos(math.radians(heading))
        y = agent.state.position.y + dist * math.sin(math.radians(heading))

        # manual collision detection
        desired_pose = (x, y, heading)

        collision_detected = False

        friends, foes = module.getMod().get_friend_foe(agent)
        for f in friends:
            if f != agent:
                f_state = f.mod_state
                # we impose an order on agents to avoid deadlocks. Without this
                # two agents which spawn very close to each other can never escape
                # each other's collision radius
                if state.id > f_state.id:
                    f_pose = f_state.pose
                    dist = self.distance(desired_pose, f_pose)
                    if dist < constants.MANUAL_COLLISION_DISTANCE:
                        collision_detected = True
                        continue

        # just check for collisions with the closest enemy
        if closest_enemy:
            if not collision_detected:
                f_pose = closest_enemy.mod_state.pose
                dist = self.distance(desired_pose, f_pose)
                if dist < constants.MANUAL_COLLISION_DISTANCE:
                    collision_detected = True

        if not collision_detected:
            state.update_pose(move_by, turn_by)

        return reward

    def calculate_reward(self, agent, action, scored_hit = False):
        reward = agent.info.reward.get_instance()

        state = agent.mod_state
        friends, foes = module.getMod().get_friend_foe(agent)

        if agent.group != 'Turret' and self.hitpoints > 0 and state.total_damage >= self.hitpoints:
            return reward

        R = dict((f, 0) for f in constants.FITNESS_DIMENSIONS)
        dist_reward = lambda d: 1 / ((d * d / constants.MAX_DIST) + 1)

        R[constants.FITNESS_STAND_GROUND] = 1 - abs(action[0])

        friend = self.nearest(state.pose, friends)
        if friend:
            d = self.distance(friend.mod_state.pose, state.pose)
            R[constants.FITNESS_STICK_TOGETHER] = dist_reward(d)

        foe = self.nearest(state.pose, foes)
        if foe:
            d = self.distance(foe.mod_state.pose, state.pose)
            R[constants.FITNESS_APPROACH_ENEMY] = dist_reward(d)

        f = module.getMod().flag_loc
        if f:
            d = self.distance(state.pose, (f.x, f.y))
            R[constants.FITNESS_APPROACH_FLAG] = dist_reward(d)

        if scored_hit:
            R[constants.FITNESS_HIT_TARGET] = 1

        damage = state.update_damage()
        R[constants.FITNESS_AVOID_FIRE] = 1 - damage

        if len(reward) == 1:
            for i, f in enumerate(constants.FITNESS_DIMENSIONS):
                reward[0] += self.reward_weights[f] * R[f] / constants.FITNESS_SCALE.get(f, 1.0)
                #print f, self.reward_weights[f], R[f] / constants.FITNESS_SCALE.get(f, 1.0)
        else:
            for i, f in enumerate(constants.FITNESS_DIMENSIONS):
                reward[i] = R[f]

        return reward

    def sense(self, agent, observations):
        """
        figure out what the agent should sense
        """
        my_team = agent.get_team()
        all_friends = my_team.agents

        ax, ay = agent.state.position.x, agent.state.position.y
        cx, cy = 0.0, 0.0
        if all_friends:
            n = 0
            for f in all_friends:
                fx, fy = f.state.position.x, f.state.position.y
                if self.distance((ax, ay), (fx, fy)) <= constants.MAX_FRIEND_DISTANCE:
                    n += 1
                    cx += fx
                    cy += fy
            if n > 0:
                cx, cy = cx / n, cy / n
                fd = self.distance((ax, ay), (cx, cy))
                ah = agent.state.rotation.z
                fh = self.angle((ax, ay, ah), (cx, cy)) + 180.0
                value = 1 - (fd / constants.MAX_FRIEND_DISTANCE)
                value = max(0, min(value, 1))
                observations[constants.SENSOR_INDEX_FRIEND_RADAR[0]] = value
                observations[constants.SENSOR_INDEX_FRIEND_RADAR[1]] = fh / 360.0
        return observations

    def distance(self, a, b):
        """
        Returns the distance between positions (x-y tuples) a and b.
        """
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def angle(self, a, b):
        """
        Returns the relative angle from a looking towards b, in the interval
        [-180, +180]. a needs to be a 3-tuple (x, y, heading) and b needs to be
        an x-y tuple.
        """
        if self.distance(a, b) == 0:
            return 0
        rh = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) - a[2]
        if rh < -180:
            rh += 360
        if rh > 180:
            rh -= 360
        return rh

    def nearest(self, loc, agents):
        """
        Returns the nearest agent to a particular location.
        """
        # TODO: this needs to only be computed once per tick, not per agent
        if not agents:
            return None
        nearest = None
        min_dist = self.MAX_DIST * 5
        for agent in agents:
            d = self.distance(loc, agent.mod_state.pose)
            if 0 < d < min_dist:
                nearest = agent
                min_dist = d
        return nearest

    def set_animation(self, agent, state, animation):
        """
        Sets current animation
        """
        if agent.state.animation != animation:
            agent.state.animation = animation

    def is_episode_over(self, agent):
        """
        is the current episode over for the agent?
        """
        if agent.group == 'Turret':
            return False

        state = agent.mod_state
        dead = self.hitpoints > 0 and state.total_damage >= self.hitpoints
        old = self.lifetime > 0 and agent.step > 0 and 0 == agent.step % self.lifetime

        return dead or old
    
    def get_hitpoints(self, agent):
        damage = agent.mod_state.total_damage
        if self.hitpoints > 0 and damage >= 0:
            return float(self.hitpoints-damage)/self.hitpoints
        else:
            return 0

    def cleanup(self):
        """
        cleanup the world
        """
        common.killScript((constants.MENU_JAR, constants.MENU_CLASS))
        return True
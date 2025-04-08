import os
import json
from typing import List
from dataclasses import dataclass, field, asdict
from datetime import timedelta
from PIL import Image
import imagehash

@dataclass
class Frame:
    filename: str
    timestamp: float  # seconds
    hash: str

@dataclass
class FrameGroup:
    id: str
    frames: List[Frame] = field(default_factory=list)

    def sort_frames(self):
        self.frames.sort(key=lambda f: f.timestamp)

    @property
    def start_time(self):
        return self.frames[0].timestamp if self.frames else None

    @property
    def end_time(self):
        return self.frames[-1].timestamp if self.frames else None

@dataclass
class Scene:
    id: str
    groups: List[FrameGroup] = field(default_factory=list)

    @property
    def start_time(self):
        return self.groups[0].start_time if self.groups else None

    @property
    def end_time(self):
        return max(group.end_time for group in self.groups) if self.groups else None

@dataclass
class GroupOutput:
    timestamp: float
    frames: List[str]

@dataclass
class SceneOutput:
    timestamp: float
    groups: List[GroupOutput] = field(default_factory=list)

@dataclass
class SceneManifest:
    scenes: List[SceneOutput] = field(default_factory=list)

def compute_phash(image_path):
    image = Image.open(image_path)
    return str(imagehash.phash(image))

def load_frames_from_directory(directory: str) -> List[Frame]:
    frames = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            timestamp = float(filename.split('_')[1].replace('.jpg', '').replace('.png', ''))
            path = os.path.join(directory, filename)
            phash = compute_phash(path)
            frames.append(Frame(filename=filename, timestamp=timestamp, hash=phash))
    return frames

def hamming_distance(hash1, hash2):
    return bin(int(str(hash1), 16) ^ int(str(hash2), 16)).count('1')

def group_by_phash_similarity(frames: List[Frame], threshold: int = 6) -> List[FrameGroup]:
    groups = []
    assigned = set()
    for i, frame in enumerate(frames):
        if frame.filename in assigned:
            continue
        group = FrameGroup(id=f"group_{frame.timestamp}", frames=[frame])
        assigned.add(frame.filename)
        for other in frames[i+1:]:
            if other.filename in assigned:
                continue
            if hamming_distance(frame.hash, other.hash) <= threshold:
                group.frames.append(other)
                assigned.add(other.filename)
        group.sort_frames()
        groups.append(group)
    return groups

def filter_small_groups(groups: List[FrameGroup], min_group_size: int = 2) -> List[FrameGroup]:
    return [g for g in groups if len(g.frames) >= min_group_size]

def split_groups_by_time_gap(groups: List[FrameGroup], max_gap: float = 1.0, min_group_size: int = 2) -> List[FrameGroup]:
    result = []
    for group in groups:
        if len(group.frames) < 2:
            result.append(group)
            continue
        group.sort_frames()
        current = [group.frames[0]]
        for i in range(1, len(group.frames)):
            if group.frames[i].timestamp - group.frames[i - 1].timestamp > max_gap:
                if len(current) >= min_group_size:
                    new_group = FrameGroup(id=f"group_{current[0].timestamp}", frames=current.copy())
                    new_group.sort_frames()
                    result.append(new_group)
                current = []
            current.append(group.frames[i])
        if len(current) >= min_group_size:
            new_group = FrameGroup(id=f"group_{current[0].timestamp}", frames=current)
            new_group.sort_frames()
            result.append(new_group)
    return result

def merge_groups_into_scenes(groups: List[FrameGroup], max_scene_gap: float = 2.0) -> List[Scene]:
    scenes = []
    groups.sort(key=lambda g: g.start_time)
    assigned = set()
    for i, group in enumerate(groups):
        if group.id in assigned:
            continue
        scene = Scene(id=f"scene_{group.start_time}", groups=[group])
        assigned.add(group.id)
        last_end = group.end_time
        for j in range(i + 1, len(groups)):
            if groups[j].id in assigned:
                continue
            if 0 <= groups[j].start_time - last_end <= max_scene_gap:
                scene.groups.append(groups[j])
                assigned.add(groups[j].id)
                last_end = max(last_end, groups[j].end_time)
        scenes.append(scene)
    return scenes

def build_scene_manifest(scenes: List[Scene]) -> SceneManifest:
    manifest = SceneManifest()
    for scene in scenes:
        scene_output = SceneOutput(timestamp=scene.start_time)
        for group in scene.groups:
            group_output = GroupOutput(
                timestamp=group.start_time,
                frames=[frame.filename for frame in group.frames]
            )
            scene_output.groups.append(group_output)
        manifest.scenes.append(scene_output)
    return manifest

def process_frames(directory: str, output_manifest_path: str):
    print("Loading frames...")
    frames = load_frames_from_directory(directory)
    print(f"Loaded {len(frames)} frames.")

    print("Grouping by pHash similarity...")
    initial_groups = group_by_phash_similarity(frames)
    print(f"Initial groups: {len(initial_groups)}")

    filtered_groups = filter_small_groups(initial_groups)
    print(f"Filtered groups: {len(filtered_groups)}")

    split_groups = split_groups_by_time_gap(filtered_groups)
    print(f"Split groups: {len(split_groups)}")

    scenes = merge_groups_into_scenes(split_groups)
    print(f"Total scenes: {len(scenes)}")

    print("Writing scene manifest...")
    manifest = build_scene_manifest(scenes)
    with open(output_manifest_path, 'w') as f:
        json.dump(asdict(manifest), f, indent=2)
    print(f"Manifest written to {output_manifest_path}")

if __name__ == '__main__':
    process_frames('./output_frames', './scene_manifest.json')

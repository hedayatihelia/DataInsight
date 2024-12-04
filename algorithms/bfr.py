import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Cluster:    
    def __init__(self, centroid):
        self.centroid = centroid
        self.discard_set = []
        self.retained_set = []
        self.compressed_set = []

    def update_centroid(self):
        if self.discard_set:
            self.centroid = calculate_centroid(self.discard_set)
    
    def summerize_CS(self):
        if self.compressed_set:
            n = len(self.compressed_set)
            sum_points = np.sum(self.compressed_set, axis=0)
            sumsq_points = np.sum(np.square(self.compressed_set), axis=0)
            self.compression_summary = {
                'n': n,
                'sum': sum_points.tolist(),
                'sumsq': sumsq_points.tolist()
            }

def initialize_clusters(data, k):
    return [Cluster(point) for point in data[:k]]

def find_closest_cluster(clusters, point):
    return min(clusters, key=lambda cluster: distance(cluster.centroid, point))

def distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))

def calculate_centroid(points):
    if len(points) == 0:
        return None
    return list(np.mean(points, axis=0))

def handle_compression_set(compression_set_summary, point, threshold):
    for cs in compression_set_summary:
        cs_centroid = np.array(cs['sum']) / cs['n']
        if np.linalg.norm(cs_centroid - point) < threshold:
            cs['n'] += 1
            cs['sum'] = np.add(cs['sum'], point).tolist()
            cs['sumsq'] = np.add(cs['sumsq'], np.square(point)).tolist()
            return
    new_cs = {
        'n': 1,
        'sum': point.tolist(),
        'sumsq': np.square(point).tolist()
    }
    compression_set_summary.append(new_cs)

def should_compress(compression_set_summary, point, threshold):
    for cs_summary in compression_set_summary:
        cs_centroid = np.array(cs_summary['sum']) / cs_summary['n']
        if distance(cs_centroid - point) < threshold:
            return True
    return False

def reassign_retained_points(clusters, compression_set_summary, threshold):
    for cluster in clusters:
        new_retained_set = []
        for point in cluster.retained_set:
            closest_cluster = find_closest_cluster(clusters, point)
            dist_to_centroid = np.linalg.norm(closest_cluster.centroid - point)
            if dist_to_centroid < threshold:
                closest_cluster.discard_set.append(point)
            elif should_compress(compression_set_summary, point, threshold):
                handle_compression_set(compression_set_summary, point, threshold)
            else:
                new_retained_set.append(point)
        cluster.retained_set = new_retained_set

def BFR(data, k, threshold):
    clusters = initialize_clusters(data, k)
    compression_set_summary = []
    
    for point in data[k:]:
        closest_cluster = find_closest_cluster(clusters, point)
        if distance(closest_cluster.centroid, point) < threshold:
            closest_cluster.discard_set.append(point)
        elif should_compress(compression_set_summary, point, threshold):
            handle_compression_set(compression_set_summary, point, threshold)
        else:
            closest_cluster.retained_set.append(point)
    reassign_retained_points(clusters, compression_set_summary, threshold)
    for cluster in clusters:
        cluster.update_centroid()
    for cs_summary in compression_set_summary:
        cs_summary['centroid'] = np.array(cs_summary['sum']) / cs_summary['n']
    
    return clusters

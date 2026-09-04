import pandas as pd
import networkx as nx
import joblib
import os

class VendorCollusionGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def build_graph(self, df: pd.DataFrame, project_col: str, vendor_col: str):
        """Builds a bipartite graph connecting projects and vendors"""
        print("Building Vendor Collusion Graph...")
        edges = list(zip(df[project_col], df[vendor_col]))
        self.graph.add_edges_from(edges)
        
    def analyze_centrality(self) -> dict:
        """Calculates degree centrality to identify highly connected (suspicious) vendors/projects"""
        print("Calculating degree centrality...")
        return nx.degree_centrality(self.graph)

    def identify_clusters(self) -> list:
        """Identifies connected components that might represent vendor cartels"""
        print("Identifying connected components...")
        return list(nx.connected_components(self.graph))

    def get_high_risk_vendors(self, centrality_threshold: float = 0.05) -> list:
        centrality = self.analyze_centrality()
        return [node for node, score in centrality.items() if score > centrality_threshold]

    def save(self, filepath: str):
        """Save the graph and module using joblib"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)
        print(f"Vendor Graph model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str):
        """Load the model using joblib"""
        return joblib.load(filepath)

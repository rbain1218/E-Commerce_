import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Product

def get_similar_products(product_id, num_recommendations=4):
    """
    Returns a list of Product instances that are most similar to the given product_id
    based on their title, description, and category.
    """
    try:
        # Fetch all products from DB
        products = Product.objects.all().select_related('category')
        
        if products.count() < 2:
            return []
            
        # Build dataset
        data = []
        for p in products:
            category_name = p.category.name if p.category else ""
            # Combining text fields to create a rich 'content' feature
            content = f"{p.title} {category_name} {p.description}"
            data.append({
                'id': p.id,
                'content': content
            })
            
        df = pd.DataFrame(data)
        
        # Initialize TF-IDF Vectorizer to remove basic english stop words
        tfidf = TfidfVectorizer(stop_words='english')
        
        # Fit and Transform the content
        tfidf_matrix = tfidf.fit_transform(df['content'])
        
        # Compute Cosine Similarity
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        # Find index of the target product
        try:
            idx = df.index[df['id'] == product_id].tolist()[0]
        except IndexError:
            return [] # Product not found in DataFrame
            
        # Get similarity scores for the target product
        sim_scores = list(enumerate(cosine_sim[idx]))
        
        # Sort products based on similarity scores (highest to lowest)
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get the indices of the most similar products (skip the first one as it is the product itself)
        similar_indices = [i[0] for i in sim_scores[1:num_recommendations+1]]
        
        # Extract product IDs
        similar_product_ids = df.iloc[similar_indices]['id'].tolist()
        
        # Fetch product instances from DB (preserving the ordered similarity)
        # We need to maintain the order we got from ML model
        preserved_order = models.Case(*[models.When(pk=pk, then=pos) for pos, pk in enumerate(similar_product_ids)])
        similar_products = Product.objects.filter(id__in=similar_product_ids).order_by(preserved_order)
        
        return similar_products
        
    except Exception as e:
        print(f"Error in recommendation engine: {e}")
        return []

from django.db import models

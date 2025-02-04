import React, { useState, useEffect } from "react";
import { Container, Typography, TextField, Button, Card, CardMedia, CardContent, Grid } from "@mui/material";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const ProductSearchPage = () => {
  const [product, setProduct] = useState("");
  const [results, setResults] = useState([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const navigate = useNavigate();


  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
    } else {
      setIsAuthenticated(true);
    }
  }, [navigate]);

  const handleSearch = () => {
    const token = localStorage.getItem("token"); 
    if (!token) {
      console.error("No token found, user not authenticated");
      return;
    }
  
    axios.post(
      "http://127.0.0.1:5000/search", 
      { product_name: product },
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        }
      }
    )
    .then((res) => setResults(res.data))
    .catch((err) => console.error("Search error:", err.response?.data || err.message));
  };
  

  const addToWishlist = async (product) => {
    const token = localStorage.getItem("token"); 
    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/wishlist",
        {
          price: product.price,
          link: product.link,
          image: product.image,
          description: product.description,
          site: product.site
        },
        {
          headers: {
            "Authorization": `Bearer ${token}`,  
          },
          // withCredentials: true,  
          }
      );
      console.log("Product added to wishlist", response.data);
    } catch (error) {
      console.error("Error adding to wishlist:", error);
    }
  };

  return (
    <Container sx={{ textAlign: "center", mt: 5 }}>
      <Typography variant="h4" color="primary" gutterBottom>
        Product Search
      </Typography>
      <TextField
        label="Enter product name"
        variant="outlined"
        fullWidth
        value={product}
        onChange={(e) => setProduct(e.target.value)}
        sx={{ mb: 2 }}
      />
      <Button variant="contained" color="primary" onClick={handleSearch}>
        Search
      </Button>

      <Grid container spacing={2} justifyContent="center" sx={{ mt: 3 }}>
        {results.map((item, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card sx={{ maxWidth: 300, m: "auto" }}>
              <CardMedia component="img" height="200" image={item.image} alt={item.description} sx={{ objectFit: "contain" }}/>
              <CardContent>
                <Typography variant="h6">{item.description}</Typography>
                <Typography color="textSecondary">{item.price}</Typography>
                <Button variant="contained" color="primary" href={item.link} target="_blank">
                  View {item.site}
                </Button>
                <Button variant="outlined" color="secondary" onClick={() => addToWishlist(item)}>
                  Add to Wishlist
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default ProductSearchPage;

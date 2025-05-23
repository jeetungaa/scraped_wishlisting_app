import React, { useEffect, useState } from "react";
import { Container, Typography, Button, Box, Card, CardContent, CardMedia, IconButton } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import DeleteIcon from "@mui/icons-material/Delete";

const WishlistPage = () => {
  const [wishlist, setWishlist] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchWishlist();
  }, []);

  const fetchWishlist = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://127.0.0.1:5000/wishlist", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setWishlist(response.data);
    } catch (error) {
      console.error("Error fetching wishlist:", error);
    }
  };

  const handleDelete = async (itemId) => {
    try {
      const token = localStorage.getItem("token");
      await axios.delete(`http://127.0.0.1:5000/wishlist/${itemId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      // Refresh the wishlist after deletion
      fetchWishlist();
    } catch (error) {
      console.error("Error deleting item:", error);
    }
  };

  return (
    <Container sx={{ textAlign: "center", mt: 5 }}>
      <Typography variant="h4" color="primary" gutterBottom>
        Your Wishlist
      </Typography>
      {wishlist.length === 0 ? (
        <Typography variant="body1">Your wishlist is empty.</Typography>
      ) : (
        <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 3 }}>
          {wishlist.map((item, index) => (
            <Card key={index} sx={{ maxWidth: 300, mx: "auto", position: "relative" }}>
              <IconButton 
                aria-label="delete" 
                onClick={() => handleDelete(item.id)}
                sx={{ 
                  position: "absolute", 
                  right: 8, 
                  top: 8, 
                  color: "error.main",
                  backgroundColor: "background.paper",
                  '&:hover': {
                    backgroundColor: "error.main",
                    color: "white"
                  }
                }}
              >
                <DeleteIcon />
              </IconButton>
              <CardMedia component="img" height="150" image={item.image} alt={item.description} sx={{ objectFit: "contain" }} />
              <CardContent>
                <Typography variant="h6">{item.description}</Typography>
                <Typography variant="body2">{item.price}</Typography>
                <Button variant="contained" color="secondary" href={item.link} target="_blank" sx={{ mt: 1 }}>
                  View {item.site}
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
      <Box sx={{ mt: 3 }}>
        <Button variant="contained" color="primary" onClick={() => navigate("/search")}>
          Back to Search
        </Button>
        <Button variant="contained" color="error" sx={{ ml: 2 }} onClick={() => {
          localStorage.removeItem("token"); 
          navigate("/login"); 
        }}>
          Logout
        </Button>
      </Box>
    </Container>
  );
};

export default WishlistPage;
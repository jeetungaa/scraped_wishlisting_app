import React, { useEffect, useState } from "react";
import { Container, Typography, Button, Box, Card, CardContent, CardMedia } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

const WishlistPage = () => {
  const [wishlist, setWishlist] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
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
    fetchWishlist();
  }, []);

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
            <Card key={index} sx={{ maxWidth: 300, mx: "auto" }}>
              <CardMedia component="img" height="150" image={item.image} alt={item.description} sx={{ objectFit: "contain" }} />
              <CardContent>
                <Typography variant="h6">{item.description}</Typography>
                <Typography variant="body2">{item.price}</Typography>
                <Button variant="contained" color="secondary" href={item.link} target="_blank">
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


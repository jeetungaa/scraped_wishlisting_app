import React from "react";
import { Container, Typography, Button, Box } from "@mui/material";
import { Link } from "react-router-dom";

const Home = () => {
  return (
    <Container sx={{ textAlign: "center", mt: 5 }}>
      <Typography variant="h3" color="primary" gutterBottom>
        Welcome to Price Compare
      </Typography>
      <Typography variant="h6" color="textSecondary" gutterBottom>
        Compare prices from Amazon and Flipkart easily!
      </Typography>
      <Box mt={3}>
        <Button variant="contained" color="primary" size="large" component={Link} to="/search" sx={{ mx: 1 }}>
          Start Searching
        </Button>
        <Button variant="outlined" color="secondary" size="large" component={Link} to="/wishlist" sx={{ mx: 1 }}>
          View Wishlist
        </Button>
      </Box>
    </Container>
  );
};

export default Home;

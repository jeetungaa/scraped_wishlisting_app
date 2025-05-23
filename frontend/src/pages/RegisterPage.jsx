import React, { useState } from "react";
import { Container, Typography, TextField, Button, Box, Alert } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

const RegisterPage = () => {
  const [credentials, setCredentials] = useState({ username: "", password: ""});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    try {
      const response = await axios.post("http://127.0.0.1:5000/register", credentials);
      if (response.data.success) {
        setSuccess("Registration successful! Redirecting to login...");
        setTimeout(() => navigate("/login"), 2000);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError("Registration failed. Please try again.");
    }
  };

  return (
    <Container sx={{ textAlign: "center", mt: 5, maxWidth: "400px" }}>
      <Typography variant="h4" color="primary" gutterBottom>
        Register
      </Typography>
      {error && <Alert severity="error">{error}</Alert>}
      {success && <Alert severity="success">{success}</Alert>}
      <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <TextField
          label="Username"
          variant="outlined"
          name="username"
          value={credentials.username}
          onChange={handleChange}
          required
        />
        {/* <TextField
          label="Email"
          variant="outlined"
          type="email"
          name="email"
          value={credentials.email}
          onChange={handleChange}
          required
        /> */}
        <TextField
          label="Password"
          variant="outlined"
          type="password"
          name="password"
          value={credentials.password}
          onChange={handleChange}
          required
        />
        <Button variant="contained" color="primary" type="submit">
          Register
        </Button>
      </Box>
      <Typography variant="body2" sx={{ mt: 2 }}>
        Already have an account? <Link to="/login">Login here</Link>
      </Typography>
    </Container>
  );
};

export default RegisterPage;

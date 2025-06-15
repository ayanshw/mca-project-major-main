function openForm() {
  document.getElementById("myForm").style.display = "block";
}

function closeForm() {
  document.getElementById("myForm").style.display = "none";
}

function login(){
  email= document.getElementById("emailLogin").value;
  password= document.getElementById("passwordLogin").value;
  if (email && password) {
    const uri= "/login";
    const data = {
      "email": email,
      "password": password
    };

  console.log("Login data:", data);
    fetch(uri, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    }).then(response => {
      if (response.status === 200) {
       
        window.location.href = "/dashboard/";
         // Redirect to home page on successful login
        // Handle successful login
      } else {
        // Handle login error
        alert("Login failed. Please check your credentials.");
      }
    });
  }
}
resource "aws_security_group" "example" {
  name        = "example-security-group"
  description = "Allow SSH access"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow access from anywhere; for more security, specify specific IPs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "example-security-group"
  }
}


resource "aws_instance" "example" {
  ami           = "ami-0862be96e41dcbf74" # Change to your preferred AMI
  instance_type = "t2.micro"
  key_name = "ec2DC"
  security_groups = [aws_security_group.example.name]

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update >> /tmp/logspython.txt
              sudo apt-get install -y python3 curl git pip python3-venv >> /tmp/logspython.txt
              git clone https://github.com/cabbagec2hlbGwK/gateway_server >> /tmp/logspython.txt
              sudo python3 -m venv /gateway_server/env 
              echo "done working on the env ______________"
              sudo /gateway_server/env/bin/pip install -r /gateway_server/requirements.txt >> /tmp/logspython.txt
              echo "done working on the installed all the pip packages ______________"
              sudo /gateway_server/env/bin/python3 /gateway_server/reciver.py >> /tmp/logspython.txt
              EOF

  tags = {
    Name = "example-instance"
  }
}

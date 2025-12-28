from fastmcp import FastMCP
import random
import json

# create mcp server 
mcp = FastMCP(name="simple calulator server")

@mcp.tool()
def add(a:float,b:float) -> float:
    """
    Add two number and returns the result as floting point value
    
    :param a: first number of addition
    :type a: float
    :param b: second number of addition
    :type b: float
    :return: returns the addition of both given number i.e. a,b
    :rtype: float
    """
    return a+b

@mcp.tool()
def random_number(min_val:int=1,max_val:int=100)->int:
    """
    generate a random number withing given range 
    
    :param min_val: minimum value defualt to 1
    :type min_val: int
    :param max_val: maxinum value defualt to 100
    :type max_val: int
    :return: a random number between min_val and max_val
    :rtype: int
    """
    return random.randint(min_val,max_val)


#Resource: server information 
@mcp.resource("info://server")
def server_info() ->str:
    """Get information about server """
    info = {
        "name":"Simple calculator server",
        "version":"1.0.0",
        "description":"A basic MCP server with math tools",
        "tools":["add","random_number"],
        "author":"Bhushan Joshi"
    }
    return json.dumps(info,indent=2)


if __name__ == "__main__":
    # mcp.run() if no transport is defined then it means that this is STDIO
    mcp.run(transport="http", host="0.0.0.0",port="8000")
    # we onlyneed to change the transport layer everything is same 

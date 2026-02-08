from fastapi import Header, HTTPException, Depends
from typing import Annotated
from database import supabase

async def get_current_user(authorization: Annotated[str | None, Header()] = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")

    try:
        # Expecting "Bearer <token>"
        token = authorization.split(" ")[1]
        user = await supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid Token")
        return user.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

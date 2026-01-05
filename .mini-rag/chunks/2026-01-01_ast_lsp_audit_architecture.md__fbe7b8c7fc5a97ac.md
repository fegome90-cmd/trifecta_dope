### 3.3 Examples
| URI | Validity | Intent |
| :--- | :--- | :--- |
| `sym://python/mod/user_model` | **VALID** | File Skeleton (`user_model.py`) |
| `sym://python/type/user_model/User` | **VALID** | Class Skeleton (`class User` in `user_model.py`) |
| `sym://python/type/user_model/User#get_email` | **VALID** | Method Snippet |
| `sym://python/User` | **INVALID** | Missing Kind (`mod` or `type`) |
| `sym://python/mod/User` | **VALID** | Looks for file `User.py` |

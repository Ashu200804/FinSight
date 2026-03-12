from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.entity import Entity, LoanType
from app.models.document import Document
from app.models.entity_ownership import EntityOwnership
from app.schemas.entity import EntityCreate, EntityUpdate, EntityResponse, EntityDraftResponse
from app.database.config import get_db
from app.utils.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/entity", tags=["entity"])
security = HTTPBearer()

def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> int:
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return int(payload.get("sub"))


def ensure_entity_ownership(db: Session, entity_id: int, user_id: int) -> None:
    existing = db.query(EntityOwnership).filter(
        EntityOwnership.entity_id == entity_id,
        EntityOwnership.user_id == user_id,
    ).first()
    if existing:
        return

    db.add(EntityOwnership(entity_id=entity_id, user_id=user_id))
    db.commit()


def get_owned_entity(db: Session, entity_id: int, user_id: int):
    ownership = db.query(EntityOwnership).filter(
        EntityOwnership.entity_id == entity_id,
        EntityOwnership.user_id == user_id,
    ).first()
    if ownership:
        return db.query(Entity).filter(Entity.id == entity_id).first()

    latest_user_doc = db.query(Document).filter(
        Document.entity_id == entity_id,
        Document.uploaded_by == user_id,
    ).order_by(Document.upload_time.desc(), Document.id.desc()).first()

    if latest_user_doc:
        ensure_entity_ownership(db=db, entity_id=entity_id, user_id=user_id)
        return db.query(Entity).filter(Entity.id == entity_id).first()

    return None

@router.post("/create", response_model=EntityDraftResponse)
def create_entity(
    entity_data: EntityCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Create a new entity (initially as draft)"""
    
    # Extract company details if provided
    company_data = entity_data.company_details.model_dump() if entity_data.company_details else {}
    loan_data = entity_data.loan_details.model_dump() if entity_data.loan_details else {}
    
    # Check if CIN already exists
    if company_data.get("cin"):
        existing_cin = db.query(Entity).filter(Entity.cin == company_data["cin"]).first()
        if existing_cin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entity with this CIN already exists"
            )
    
    # Create new entity
    new_entity = Entity(
        company_name=company_data.get("company_name"),
        cin=company_data.get("cin"),
        pan=company_data.get("pan"),
        sector=company_data.get("sector"),
        subsector=company_data.get("subsector"),
        turnover=company_data.get("turnover"),
        address=company_data.get("address"),
        loan_type=loan_data.get("loan_type"),
        loan_amount=loan_data.get("loan_amount"),
        tenure=loan_data.get("tenure"),
        interest_rate=loan_data.get("interest_rate"),
        purpose_of_loan=loan_data.get("purpose_of_loan"),
        is_draft="true" if entity_data.is_draft else "false"
    )
    
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    ensure_entity_ownership(db=db, entity_id=new_entity.id, user_id=user_id)
    
    return {
        "id": new_entity.id,
        "company_name": new_entity.company_name,
        "cin": new_entity.cin,
        "pan": new_entity.pan,
        "sector": new_entity.sector,
        "subsector": new_entity.subsector,
        "turnover": new_entity.turnover,
        "address": new_entity.address,
        "loan_type": new_entity.loan_type,
        "loan_amount": new_entity.loan_amount,
        "tenure": new_entity.tenure,
        "interest_rate": new_entity.interest_rate,
        "purpose_of_loan": new_entity.purpose_of_loan,
        "is_draft": new_entity.is_draft == "true",
        "created_at": new_entity.created_at,
        "updated_at": new_entity.updated_at
    }

@router.get("/latest", response_model=EntityDraftResponse)
def get_latest_entity(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Retrieve latest entity for onboarding skip after sign-in"""
    latest_owned = db.query(EntityOwnership).filter(
        EntityOwnership.user_id == user_id
    ).order_by(EntityOwnership.created_at.desc(), EntityOwnership.id.desc()).first()

    if latest_owned:
        entity = db.query(Entity).filter(Entity.id == latest_owned.entity_id).first()
        if entity:
            return {
                "id": entity.id,
                "company_name": entity.company_name,
                "cin": entity.cin,
                "pan": entity.pan,
                "sector": entity.sector,
                "subsector": entity.subsector,
                "turnover": entity.turnover,
                "address": entity.address,
                "loan_type": entity.loan_type,
                "loan_amount": entity.loan_amount,
                "tenure": entity.tenure,
                "interest_rate": entity.interest_rate,
                "purpose_of_loan": entity.purpose_of_loan,
                "is_draft": entity.is_draft == "true",
                "created_at": entity.created_at,
                "updated_at": entity.updated_at
            }

    latest_user_doc = db.query(Document).filter(
        Document.uploaded_by == user_id
    ).order_by(Document.upload_time.desc(), Document.id.desc()).first()

    if latest_user_doc:
        entity = db.query(Entity).filter(Entity.id == latest_user_doc.entity_id).first()
        if entity:
            ensure_entity_ownership(db=db, entity_id=entity.id, user_id=user_id)
            return {
                "id": entity.id,
                "company_name": entity.company_name,
                "cin": entity.cin,
                "pan": entity.pan,
                "sector": entity.sector,
                "subsector": entity.subsector,
                "turnover": entity.turnover,
                "address": entity.address,
                "loan_type": entity.loan_type,
                "loan_amount": entity.loan_amount,
                "tenure": entity.tenure,
                "interest_rate": entity.interest_rate,
                "purpose_of_loan": entity.purpose_of_loan,
                "is_draft": entity.is_draft == "true",
                "created_at": entity.created_at,
                "updated_at": entity.updated_at
            }

    entity = db.query(Entity).outerjoin(
        EntityOwnership,
        EntityOwnership.entity_id == Entity.id,
    ).filter(
        EntityOwnership.id.is_(None)
    ).order_by(Entity.updated_at.desc(), Entity.id.desc()).first()

    if entity:
        ensure_entity_ownership(db=db, entity_id=entity.id, user_id=user_id)

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entities found"
        )

    return {
        "id": entity.id,
        "company_name": entity.company_name,
        "cin": entity.cin,
        "pan": entity.pan,
        "sector": entity.sector,
        "subsector": entity.subsector,
        "turnover": entity.turnover,
        "address": entity.address,
        "loan_type": entity.loan_type,
        "loan_amount": entity.loan_amount,
        "tenure": entity.tenure,
        "interest_rate": entity.interest_rate,
        "purpose_of_loan": entity.purpose_of_loan,
        "is_draft": entity.is_draft == "true",
        "created_at": entity.created_at,
        "updated_at": entity.updated_at
    }

@router.get("/{entity_id}", response_model=EntityDraftResponse)
def get_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Retrieve entity by ID"""
    entity = get_owned_entity(db=db, entity_id=entity_id, user_id=user_id)
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found"
        )
    
    return {
        "id": entity.id,
        "company_name": entity.company_name,
        "cin": entity.cin,
        "pan": entity.pan,
        "sector": entity.sector,
        "subsector": entity.subsector,
        "turnover": entity.turnover,
        "address": entity.address,
        "loan_type": entity.loan_type,
        "loan_amount": entity.loan_amount,
        "tenure": entity.tenure,
        "interest_rate": entity.interest_rate,
        "purpose_of_loan": entity.purpose_of_loan,
        "is_draft": entity.is_draft == "true",
        "created_at": entity.created_at,
        "updated_at": entity.updated_at
    }

@router.put("/{entity_id}", response_model=EntityDraftResponse)
def update_entity(
    entity_id: int,
    entity_data: EntityUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update entity (autosave draft)"""
    entity = get_owned_entity(db=db, entity_id=entity_id, user_id=user_id)
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found"
        )
    
    # Update company details if provided
    company_data = entity_data.company_details
    if company_data:
        entity.company_name = company_data.company_name or entity.company_name
        entity.cin = company_data.cin or entity.cin
        entity.pan = company_data.pan or entity.pan
        entity.sector = company_data.sector or entity.sector
        entity.subsector = company_data.subsector or entity.subsector
        entity.turnover = company_data.turnover if company_data.turnover is not None else entity.turnover
        entity.address = company_data.address or entity.address
    
    # Update loan details if provided
    loan_data = entity_data.loan_details
    if loan_data:
        entity.loan_type = loan_data.loan_type or entity.loan_type
        entity.loan_amount = loan_data.loan_amount if loan_data.loan_amount is not None else entity.loan_amount
        entity.tenure = loan_data.tenure if loan_data.tenure is not None else entity.tenure
        entity.interest_rate = loan_data.interest_rate if loan_data.interest_rate is not None else entity.interest_rate
        entity.purpose_of_loan = loan_data.purpose_of_loan or entity.purpose_of_loan
    
    entity.is_draft = "true" if entity_data.is_draft else "false"
    
    db.commit()
    db.refresh(entity)
    
    return {
        "id": entity.id,
        "company_name": entity.company_name,
        "cin": entity.cin,
        "pan": entity.pan,
        "sector": entity.sector,
        "subsector": entity.subsector,
        "turnover": entity.turnover,
        "address": entity.address,
        "loan_type": entity.loan_type,
        "loan_amount": entity.loan_amount,
        "tenure": entity.tenure,
        "interest_rate": entity.interest_rate,
        "purpose_of_loan": entity.purpose_of_loan,
        "is_draft": entity.is_draft == "true",
        "created_at": entity.created_at,
        "updated_at": entity.updated_at
    }
